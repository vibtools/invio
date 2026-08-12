from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import struct
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

IVX_FORMAT_VERSION = 1
IVX_MARKER_FILENAME = ".invio-ivx.json"
IVX_REQUIRED_MANIFEST = "provider.json"
IVX_ADAPTER_FILENAME = "adapter.py"
IVX_LOGO_FILENAME = "logo.png"
IVX_CHECKSUM_FILENAME = "SHA256SUMS.txt"

MAX_IVX_COMPRESSED_BYTES = 50 * 1024 * 1024
MAX_IVX_EXTRACTED_BYTES = 200 * 1024 * 1024
MAX_IVX_FILE_COUNT = 256
MAX_IVX_FILE_BYTES = 50 * 1024 * 1024
MAX_IVX_LOGO_BYTES = 5 * 1024 * 1024
MAX_IVX_LOGO_DIMENSION = 4096

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class IvxPackageError(ValueError):
    """Raised when an Invio Provider Extension archive is unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class IvxArchiveInspection:
    source_path: Path
    archive_sha256: str
    members: tuple[str, ...]
    manifest_bytes: bytes
    total_extracted_bytes: int
    file_count: int
    has_adapter: bool
    logo_valid: bool
    logo_warning: str = ""
    checksums_verified: bool = False


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _member_key(name: str) -> str:
    return name[:-1] if name.endswith("/") else name


def _validate_member_name(name: str) -> PurePosixPath:
    if not name or "\x00" in name:
        raise IvxPackageError("The IVX package contains an empty or invalid archive path.")
    if "\\" in name:
        raise IvxPackageError("The IVX package contains a Windows-style or UNC archive path.")
    if name.startswith("/") or name.startswith("//"):
        raise IvxPackageError("The IVX package contains an absolute archive path.")

    # Validate the raw spelling before PurePosixPath can normalize aliases such
    # as './file' or 'dir//file' into the same extraction target. Directory
    # entries may have one trailing slash; empty/dot/dot-dot components may not.
    raw_parts = name.split("/")
    if name.endswith("/"):
        raw_parts = raw_parts[:-1]
    if not raw_parts or any(part in {"", ".", ".."} for part in raw_parts):
        raise IvxPackageError("The IVX package contains an unsafe or non-canonical relative archive path.")
    if _WINDOWS_DRIVE_RE.match(raw_parts[0]):
        raise IvxPackageError("The IVX package contains a Windows drive-qualified archive path.")

    # Keep IVX paths portable and prevent Windows NTFS alternate-data-stream or
    # device-name ambiguities from materializing hidden/non-canonical entries.
    windows_forbidden = set('<>:"|?*')
    for part in raw_parts:
        if any(ord(ch) < 32 for ch in part) or any(ch in windows_forbidden for ch in part):
            raise IvxPackageError("The IVX package contains a Windows-unsafe archive path component.")
        if part.endswith((" ", ".")):
            raise IvxPackageError("The IVX package contains a non-portable trailing space or dot in an archive path.")
        stem = part.split(".", 1)[0].casefold()
        if stem in {"con", "prn", "aux", "nul", "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9", "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"}:
            raise IvxPackageError("The IVX package contains a reserved Windows device-name path component.")

    return PurePosixPath(name)


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(unix_mode)


def _read_member_limited(zf: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> bytes:
    if info.file_size > limit:
        raise IvxPackageError(f"IVX member '{info.filename}' exceeds its permitted size.")
    data = zf.read(info)
    if len(data) != info.file_size or len(data) > limit:
        raise IvxPackageError(f"IVX member '{info.filename}' has an inconsistent extracted size.")
    return data


def _valid_png(data: bytes) -> bool:
    if len(data) < 8 or data[:8] != _PNG_SIGNATURE:
        return False
    offset = 8
    saw_ihdr = False
    saw_idat = False
    saw_iend = False
    while offset < len(data):
        if offset + 12 > len(data):
            return False
        length = struct.unpack_from(">I", data, offset)[0]
        chunk_type = data[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(data):
            return False
        chunk_data = data[data_start:data_end]
        expected_crc = struct.unpack_from(">I", data, data_end)[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(chunk_data, actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            return False
        if not saw_ihdr:
            if chunk_type != b"IHDR" or length != 13:
                return False
            width, height = struct.unpack_from(">II", chunk_data, 0)
            if width <= 0 or height <= 0 or width > MAX_IVX_LOGO_DIMENSION or height > MAX_IVX_LOGO_DIMENSION:
                return False
            saw_ihdr = True
        elif chunk_type == b"IHDR":
            return False
        if chunk_type == b"IDAT":
            saw_idat = True
        if chunk_type == b"IEND":
            if length != 0:
                return False
            saw_iend = True
            offset = crc_end
            break
        offset = crc_end
    return saw_ihdr and saw_idat and saw_iend and offset == len(data)


def _validate_optional_checksums(
    zf: zipfile.ZipFile,
    infos_by_name: dict[str, zipfile.ZipInfo],
) -> bool:
    checksum_info = infos_by_name.get(IVX_CHECKSUM_FILENAME)
    if checksum_info is None:
        return False
    raw = _read_member_limited(zf, checksum_info, MAX_IVX_FILE_BYTES)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IvxPackageError("SHA256SUMS.txt must be UTF-8 text.") from exc

    expected: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip("\r\n")
        if not line.strip():
            continue
        if "  " not in line:
            raise IvxPackageError(f"SHA256SUMS.txt line {line_number} is malformed.")
        digest_text, member_name = line.split("  ", 1)
        digest_text = digest_text.strip()
        member_name = member_name.strip()
        if not _SHA256_RE.fullmatch(digest_text) or not member_name:
            raise IvxPackageError(f"SHA256SUMS.txt line {line_number} is malformed.")
        _validate_member_name(member_name)
        if member_name == IVX_CHECKSUM_FILENAME or member_name in expected:
            raise IvxPackageError("SHA256SUMS.txt contains an invalid or duplicate checksum entry.")
        expected[member_name] = digest_text.lower()

    actual_names = {
        name
        for name, info in infos_by_name.items()
        if not info.is_dir() and name != IVX_CHECKSUM_FILENAME
    }
    if set(expected) != actual_names:
        raise IvxPackageError("SHA256SUMS.txt must cover every regular package file except itself exactly once.")

    for name in sorted(actual_names):
        digest = hashlib.sha256()
        with zf.open(infos_by_name[name], "r") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected[name]:
            raise IvxPackageError(f"SHA256 checksum verification failed for '{name}'.")
    return True


def inspect_ivx(path: str | Path) -> IvxArchiveInspection:
    source = Path(path)
    if source.suffix.casefold() != ".ivx":
        raise IvxPackageError("Invio provider packages must use the .ivx extension.")
    try:
        archive_size = source.stat().st_size
    except OSError as exc:
        raise IvxPackageError("The selected IVX package could not be read.") from exc
    if archive_size <= 0 or archive_size > MAX_IVX_COMPRESSED_BYTES:
        raise IvxPackageError("The IVX package exceeds the 50 MB compressed-size limit or is empty.")

    archive_sha256 = _sha256_file(source)
    try:
        with zipfile.ZipFile(source, "r") as zf:
            infos = zf.infolist()
            if not infos:
                raise IvxPackageError("The IVX package is empty.")

            seen_casefold: dict[str, str] = {}
            infos_by_name: dict[str, zipfile.ZipInfo] = {}
            regular_file_count = 0
            total_extracted = 0
            for info in infos:
                # ZipInfo.filename is platform-normalized by Python. On Windows,
                # a raw backslash in the ZIP central directory is converted to
                # a forward slash before callers see filename. orig_filename
                # preserves the archive spelling and must be the security input.
                name = info.orig_filename
                _validate_member_name(name)
                if info.flag_bits & 0x1:
                    raise IvxPackageError("Encrypted IVX members are not supported.")
                if _is_symlink(info):
                    raise IvxPackageError("Symbolic links are not permitted inside IVX packages.")

                key = _member_key(name)
                folded = key.casefold()
                previous = seen_casefold.get(folded)
                if previous is not None:
                    raise IvxPackageError(
                        f"The IVX package contains duplicate or case-colliding paths: '{previous}' and '{key}'."
                    )
                seen_casefold[folded] = key
                infos_by_name[key] = info

                if info.is_dir():
                    continue
                regular_file_count += 1
                if regular_file_count > MAX_IVX_FILE_COUNT:
                    raise IvxPackageError("The IVX package exceeds the 256-file limit.")
                if info.file_size < 0 or info.file_size > MAX_IVX_FILE_BYTES:
                    raise IvxPackageError(f"IVX member '{name}' exceeds the 50 MB per-file limit.")
                total_extracted += info.file_size
                if total_extracted > MAX_IVX_EXTRACTED_BYTES:
                    raise IvxPackageError("The IVX package exceeds the 200 MB extracted-size limit.")

            manifest_info = infos_by_name.get(IVX_REQUIRED_MANIFEST)
            if manifest_info is None or manifest_info.is_dir():
                nested = any(
                    name.casefold().endswith("/provider.json")
                    for name, info in infos_by_name.items()
                    if not info.is_dir()
                )
                if nested:
                    raise IvxPackageError("provider.json must be stored at the IVX archive root; wrapper folders are not supported.")
                raise IvxPackageError("The IVX package is missing root-level provider.json.")

            # ZipFile.testzip() decompresses every member and validates CRCs.
            bad_member = zf.testzip()
            if bad_member is not None:
                raise IvxPackageError(f"The IVX package failed CRC validation at '{bad_member}'.")

            manifest_bytes = _read_member_limited(zf, manifest_info, MAX_IVX_FILE_BYTES)
            try:
                json.loads(manifest_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise IvxPackageError("Root provider.json is not valid UTF-8 JSON.") from exc

            checksums_verified = _validate_optional_checksums(zf, infos_by_name)

            logo_valid = False
            logo_warning = ""
            logo_info = infos_by_name.get(IVX_LOGO_FILENAME)
            if logo_info is not None and not logo_info.is_dir():
                if logo_info.file_size > MAX_IVX_LOGO_BYTES:
                    logo_warning = "Provider logo.png exceeds the 5 MB visual-asset limit; the host fallback icon will be used."
                else:
                    logo_bytes = _read_member_limited(zf, logo_info, MAX_IVX_LOGO_BYTES)
                    if _valid_png(logo_bytes):
                        logo_valid = True
                    else:
                        logo_warning = (
                            "Provider logo.png is not a safe, structurally valid PNG within the supported dimensions; "
                            "the host fallback icon will be used."
                        )

            return IvxArchiveInspection(
                source_path=source,
                archive_sha256=archive_sha256,
                members=tuple(info.orig_filename for info in infos),
                manifest_bytes=manifest_bytes,
                total_extracted_bytes=total_extracted,
                file_count=regular_file_count,
                has_adapter=IVX_ADAPTER_FILENAME in infos_by_name and not infos_by_name[IVX_ADAPTER_FILENAME].is_dir(),
                logo_valid=logo_valid,
                logo_warning=logo_warning,
                checksums_verified=checksums_verified,
            )
    except IvxPackageError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError) as exc:
        raise IvxPackageError("The selected .ivx file is not a valid, readable ZIP-based Invio provider package.") from exc


def extract_ivx(inspection: IvxArchiveInspection, destination: Path) -> None:
    """Safely materialize a previously inspected IVX archive into staging.

    The archive is re-inspected immediately before extraction so a file changed
    between validation and materialization is rejected. Invalid optional logo
    bytes are deliberately not copied; the UI will resolve the host fallback.
    """

    source = inspection.source_path
    fresh = inspect_ivx(source)
    if (
        fresh.archive_sha256 != inspection.archive_sha256
        or fresh.members != inspection.members
        or fresh.manifest_bytes != inspection.manifest_bytes
    ):
        raise IvxPackageError("The IVX package changed after validation; import was cancelled.")

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    root_resolved = destination.resolve()
    extracted_total = 0
    try:
        with zipfile.ZipFile(source, "r") as zf:
            for info in zf.infolist():
                name = info.orig_filename
                posix = _validate_member_name(name)
                if name == IVX_LOGO_FILENAME and not fresh.logo_valid:
                    continue
                target = destination.joinpath(*posix.parts)
                target_resolved = target.resolve()
                try:
                    target_resolved.relative_to(root_resolved)
                except ValueError as exc:
                    raise IvxPackageError("The IVX package attempted to extract outside the staging directory.") from exc

                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                with zf.open(info, "r") as src, target.open("wb") as dst:
                    while True:
                        chunk = src.read(1024 * 1024)
                        if not chunk:
                            break
                        written += len(chunk)
                        extracted_total += len(chunk)
                        if written > info.file_size or written > MAX_IVX_FILE_BYTES:
                            raise IvxPackageError(f"IVX member '{name}' exceeded its declared safe size during extraction.")
                        if extracted_total > MAX_IVX_EXTRACTED_BYTES:
                            raise IvxPackageError("The IVX package exceeded its safe total extracted size during extraction.")
                        dst.write(chunk)
                if written != info.file_size:
                    raise IvxPackageError(f"IVX member '{name}' extracted to an unexpected size.")
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def write_ivx_marker(package_root: Path, *, inspection: IvxArchiveInspection) -> None:
    marker = {
        "format": "Invio Provider Extension",
        "format_version": IVX_FORMAT_VERSION,
        "source_filename": inspection.source_path.name,
        "archive_sha256": inspection.archive_sha256,
        "logo_valid": inspection.logo_valid,
        "checksums_verified": inspection.checksums_verified,
    }
    target = Path(package_root) / IVX_MARKER_FILENAME
    target.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_ivx_marker(package_root: Path) -> dict[str, object] | None:
    path = Path(package_root) / IVX_MARKER_FILENAME
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if raw.get("format") != "Invio Provider Extension" or raw.get("format_version") != IVX_FORMAT_VERSION:
        return None
    return raw
