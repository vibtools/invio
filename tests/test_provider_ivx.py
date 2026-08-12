from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch

from src.core.provider_manager import ProviderManager, ProviderManifestError
from src.core.provider_manager.ivx import IVX_MARKER_FILENAME, inspect_ivx


_ONE_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x72\x9c\x52\x67"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _manifest(provider_id: str = "ivx_provider", *, executable: bool = True, version: str = "1.0.0") -> dict:
    raw = {
        "id": provider_id,
        "name": "IVX Provider",
        "version": version,
        "description": "IVX test provider",
        "credential_fields": [],
        "account_modes": ["Default"],
        "capabilities": ["invoice"],
    }
    if executable:
        raw["runtime_adapter"] = {
            "interface_version": 1,
            "adapter_version": version,
            "entrypoint": "create_adapter",
        }
    return raw


def _checksum_text(files: dict[str, bytes]) -> bytes:
    lines = [f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(files.items())]
    return "".join(lines).encode("utf-8")


def _write_ivx(
    path: Path,
    *,
    manifest: dict | None = None,
    files: dict[str, bytes] | None = None,
    checksums: bool = False,
    custom_infos: list[tuple[zipfile.ZipInfo, bytes]] | None = None,
) -> Path:
    payload = dict(files or {})
    if manifest is not None:
        payload.setdefault("provider.json", json.dumps(manifest).encode("utf-8"))
    if checksums:
        payload["SHA256SUMS.txt"] = _checksum_text(payload)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in payload.items():
            zf.writestr(name, data)
        for info, data in custom_infos or []:
            zf.writestr(info, data)
    return path


class ProviderIvxTests(unittest.TestCase):
    def _root(self, td: str) -> Path:
        root = Path(td)
        (root / "providers" / "packages").mkdir(parents=True)
        (root / "providers" / "registry").mkdir(parents=True)
        return root

    def test_valid_ivx_import_is_available_not_installed_and_never_executes_adapter(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            ivx = Path(td) / "Provider.ivx"
            _write_ivx(
                ivx,
                manifest=_manifest(),
                files={"adapter.py": b"raise RuntimeError('must not execute during import')\n", "README.md": b"docs"},
                checksums=True,
            )
            manager = ProviderManager(root)
            imported = manager.import_ivx(ivx)
            self.assertEqual(imported.id, "ivx_provider")
            self.assertEqual([item.id for item in manager.list_available()], ["ivx_provider"])
            self.assertEqual(manager.list_installed(), [])
            package = root / "providers" / "packages" / "ivx_provider"
            self.assertTrue((package / "provider.json").is_file())
            self.assertTrue((package / "adapter.py").is_file())
            self.assertTrue((package / IVX_MARKER_FILENAME).is_file())
            self.assertIsNone(manager.get_packaged("ivx_provider"))

    def test_imported_executable_package_uses_existing_trusted_install_and_uninstall_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            ivx = Path(td) / "Provider.ivx"
            _write_ivx(ivx, manifest=_manifest(), files={"adapter.py": b"def create_adapter():\n    return None\n"})
            manager = ProviderManager(root)
            manager.import_ivx(ivx)
            validated: list[Path] = []

            def validator(_manifest, adapter_path):
                validated.append(Path(adapter_path))

            installed = manager.install_packaged("ivx_provider", allow_executable=True, adapter_validator=validator)
            self.assertEqual(installed.id, "ivx_provider")
            self.assertEqual(len(validated), 1)
            self.assertTrue(manager.external_adapter_path("ivx_provider").is_file())
            manager.uninstall("ivx_provider")
            self.assertFalse(manager.external_adapter_path("ivx_provider").exists())
            self.assertTrue((root / "providers" / "packages" / "ivx_provider" / "provider.json").is_file())
            self.assertEqual([item.id for item in manager.list_available()], ["ivx_provider"])

    def test_imported_executable_package_requires_explicit_trust_at_install(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            ivx = Path(td) / "Provider.ivx"
            _write_ivx(ivx, manifest=_manifest(), files={"adapter.py": b"pass\n"})
            manager = ProviderManager(root)
            manager.import_ivx(ivx)
            with self.assertRaisesRegex(ProviderManifestError, "Explicit trusted-code approval"):
                manager.install_packaged("ivx_provider")

    def test_legacy_manifest_only_ivx_installs_without_adapter(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            ivx = Path(td) / "ManifestOnly.ivx"
            _write_ivx(ivx, manifest=_manifest(executable=False))
            manager = ProviderManager(root)
            manager.import_ivx(ivx)
            installed = manager.install_packaged("ivx_provider")
            self.assertEqual(installed.id, "ivx_provider")
            self.assertFalse(manager.external_adapter_path("ivx_provider").exists())

    def test_builtin_package_id_cannot_be_replaced_by_ivx(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            package = root / "providers" / "packages" / "protected"
            package.mkdir()
            (package / "provider.json").write_text(json.dumps(_manifest("protected", executable=False)), encoding="utf-8")
            ivx = Path(td) / "Protected.ivx"
            _write_ivx(ivx, manifest=_manifest("protected", executable=False))
            manager = ProviderManager(root)
            with self.assertRaisesRegex(ProviderManifestError, "reserved"):
                manager.import_ivx(ivx)
            self.assertFalse((package / IVX_MARKER_FILENAME).exists())

    def test_imported_package_replacement_is_canonical_and_preserves_one_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            first = Path(td) / "First.ivx"
            second = Path(td) / "AnythingElse.ivx"
            _write_ivx(first, manifest=_manifest(version="1.0.0"), files={"adapter.py": b"# old\n"})
            _write_ivx(second, manifest=_manifest(version="2.0.0"), files={"adapter.py": b"# new\n"})
            manager = ProviderManager(root)
            manager.import_ivx(first)
            manager.import_ivx(second)
            self.assertEqual(manager.get_available("ivx_provider").version, "2.0.0")
            directories = [item.name for item in (root / "providers" / "packages").iterdir() if item.is_dir()]
            self.assertEqual(directories, ["ivx_provider"])

    def test_replacement_move_failure_restores_old_imported_package(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            first = Path(td) / "First.ivx"
            second = Path(td) / "Second.ivx"
            _write_ivx(first, manifest=_manifest(version="1.0.0"), files={"adapter.py": b"# old\n"})
            _write_ivx(second, manifest=_manifest(version="2.0.0"), files={"adapter.py": b"# new\n"})
            manager = ProviderManager(root)
            manager.import_ivx(first)
            real_replace = os.replace
            calls = {"count": 0}

            def fail_new_move(src, dst):
                src_path = Path(src)
                dst_path = Path(dst)
                if src_path.name == "package" and dst_path.name == "ivx_provider":
                    calls["count"] += 1
                    raise OSError("injected final move failure")
                return real_replace(src, dst)

            with patch("src.core.provider_manager.manager.os.replace", side_effect=fail_new_move):
                with self.assertRaises(ProviderManifestError):
                    manager.import_ivx(second)
            self.assertEqual(manager.get_available("ivx_provider").version, "1.0.0")

    def test_valid_logo_is_materialized_and_invalid_logo_uses_package_fallback_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            valid = Path(td) / "Valid.ivx"
            _write_ivx(valid, manifest=_manifest(executable=False), files={"logo.png": _ONE_PIXEL_PNG})
            manager = ProviderManager(root)
            manager.import_ivx(valid)
            self.assertTrue(manager.provider_logo_path("ivx_provider").is_file())

            invalid = Path(td) / "Invalid.ivx"
            _write_ivx(invalid, manifest=_manifest(executable=False, version="2.0"), files={"logo.png": b"not-a-png"})
            manager.import_ivx(invalid)
            self.assertIsNone(manager.provider_logo_path("ivx_provider"))
            self.assertFalse((root / "providers" / "packages" / "ivx_provider" / "logo.png").exists())

            signature_only = Path(td) / "SignatureOnly.ivx"
            _write_ivx(
                signature_only,
                manifest=_manifest(executable=False, version="3.0"),
                files={"logo.png": b"\x89PNG\r\n\x1a\nnot-a-real-png"},
            )
            manager.import_ivx(signature_only)
            self.assertIsNone(manager.provider_logo_path("ivx_provider"))

            huge_png = bytearray(_ONE_PIXEL_PNG)
            struct.pack_into(">II", huge_png, 16, 5000, 5000)
            ihdr_crc = zlib.crc32(b"IHDR")
            ihdr_crc = zlib.crc32(bytes(huge_png[16:29]), ihdr_crc) & 0xFFFFFFFF
            struct.pack_into(">I", huge_png, 29, ihdr_crc)
            huge = Path(td) / "HugeLogo.ivx"
            _write_ivx(huge, manifest=_manifest(executable=False, version="4.0"), files={"logo.png": bytes(huge_png)})
            manager.import_ivx(huge)
            self.assertIsNone(manager.provider_logo_path("ivx_provider"))

    def test_optional_sha256sums_is_verified(self):
        with tempfile.TemporaryDirectory() as td:
            ivx = Path(td) / "Checksummed.ivx"
            _write_ivx(ivx, manifest=_manifest(executable=False), files={"README.md": b"hello"}, checksums=True)
            inspection = inspect_ivx(ivx)
            self.assertTrue(inspection.checksums_verified)

    def test_bad_sha256sums_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ivx = Path(td) / "BadChecksum.ivx"
            files = {
                "provider.json": json.dumps(_manifest(executable=False)).encode(),
                "README.md": b"hello",
                "SHA256SUMS.txt": ("0" * 64 + "  provider.json\n" + "0" * 64 + "  README.md\n").encode(),
            }
            _write_ivx(ivx, files=files)
            with self.assertRaisesRegex(ValueError, "checksum"):
                inspect_ivx(ivx)

    def test_non_zip_renamed_ivx_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ivx = Path(td) / "Fake.ivx"
            ivx.write_bytes(b"not a zip")
            with self.assertRaises(ValueError):
                inspect_ivx(ivx)

    def test_unsupported_zip_compression_is_wrapped_as_ivx_validation_error(self):
        with tempfile.TemporaryDirectory() as td:
            ivx = Path(td) / "UnsupportedCompression.ivx"
            _write_ivx(ivx, files={"provider.json": b"{}"})
            payload = bytearray(ivx.read_bytes())
            local = payload.find(b"PK\x03\x04")
            central = payload.find(b"PK\x01\x02")
            self.assertGreaterEqual(local, 0)
            self.assertGreaterEqual(central, 0)
            struct.pack_into("<H", payload, local + 8, 99)
            struct.pack_into("<H", payload, central + 10, 99)
            ivx.write_bytes(payload)
            with self.assertRaisesRegex(ValueError, "valid, readable ZIP-based"):
                inspect_ivx(ivx)

    def test_missing_root_manifest_and_wrapper_folder_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "Missing.ivx"
            _write_ivx(missing, files={"README.md": b"x"})
            with self.assertRaisesRegex(ValueError, "missing root-level provider.json"):
                inspect_ivx(missing)
            wrapper = Path(td) / "Wrapper.ivx"
            _write_ivx(wrapper, files={"Zoho/provider.json": b"{}"})
            with self.assertRaisesRegex(ValueError, "wrapper folders"):
                inspect_ivx(wrapper)

    def test_executable_manifest_without_adapter_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._root(td)
            ivx = Path(td) / "MissingAdapter.ivx"
            _write_ivx(ivx, manifest=_manifest(executable=True))
            manager = ProviderManager(root)
            with self.assertRaisesRegex(ProviderManifestError, "missing root-level adapter.py"):
                manager.import_ivx(ivx)

    def test_path_traversal_absolute_windows_and_backslash_paths_are_rejected(self):
        unsafe_names = [
            "../adapter.py",
            "/absolute/provider.json",
            "C:/provider.json",
            "dir\\provider.json",
            "./alias.txt",
            "dir//alias.txt",
            "dir/file:stream",
            "CON",
            "trailing.",
            "trailing ",
        ]
        for index, unsafe in enumerate(unsafe_names):
            with self.subTest(unsafe=unsafe), tempfile.TemporaryDirectory() as td:
                ivx = Path(td) / f"Unsafe{index}.ivx"
                # ZipInfo sanitizes OS separators in its constructor on Windows.
                # Mutating the filename afterward writes the exact unsafe central-
                # directory spelling so the reader-side security check is tested
                # identically on Windows and POSIX.
                raw_info = zipfile.ZipInfo("placeholder")
                raw_info.filename = unsafe
                raw_info.orig_filename = unsafe
                _write_ivx(ivx, files={"provider.json": b"{}"}, custom_infos=[(raw_info, b"x")])
                with self.assertRaises(ValueError):
                    inspect_ivx(ivx)

    def test_symlink_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ivx = Path(td) / "Symlink.ivx"
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            _write_ivx(ivx, files={"provider.json": b"{}"}, custom_infos=[(info, b"adapter.py")])
            with self.assertRaisesRegex(ValueError, "Symbolic links"):
                inspect_ivx(ivx)

    def test_duplicate_and_case_colliding_paths_are_rejected(self):
        for left, right in [("A.txt", "a.txt"), ("same.txt", "same.txt")]:
            with self.subTest(left=left, right=right), tempfile.TemporaryDirectory() as td:
                ivx = Path(td) / "Collision.ivx"
                infos = [(zipfile.ZipInfo(left), b"a"), (zipfile.ZipInfo(right), b"b")]
                _write_ivx(ivx, files={"provider.json": b"{}"}, custom_infos=infos)
                with self.assertRaisesRegex(ValueError, "duplicate or case-colliding"):
                    inspect_ivx(ivx)

    def test_encrypted_flag_is_rejected(self):
        # Python's writer normalizes the encrypted bit away, so validate the
        # policy at the central-directory inspection boundary with a controlled
        # ZipInfo object returned by ZipFile.
        with tempfile.TemporaryDirectory() as td:
            ivx = Path(td) / "Encrypted.ivx"
            _write_ivx(ivx, files={"provider.json": b"{}"})
            original = zipfile.ZipFile.infolist

            def encrypted_infos(zf):
                infos = original(zf)
                infos[0].flag_bits |= 0x1
                return infos

            with patch("zipfile.ZipFile.infolist", encrypted_infos):
                with self.assertRaisesRegex(ValueError, "Encrypted"):
                    inspect_ivx(ivx)

    def test_resource_limits_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            ivx = Path(td) / "Limits.ivx"
            _write_ivx(ivx, files={"provider.json": b"{}", "large.bin": b"1234"})
            with patch("src.core.provider_manager.ivx.MAX_IVX_FILE_BYTES", 3):
                with self.assertRaisesRegex(ValueError, "per-file"):
                    inspect_ivx(ivx)
            with patch("src.core.provider_manager.ivx.MAX_IVX_FILE_COUNT", 1):
                with self.assertRaisesRegex(ValueError, "file limit"):
                    inspect_ivx(ivx)
            with patch("src.core.provider_manager.ivx.MAX_IVX_EXTRACTED_BYTES", 3):
                with self.assertRaisesRegex(ValueError, "extracted-size"):
                    inspect_ivx(ivx)

    def test_changed_archive_after_inspection_is_rejected(self):
        from src.core.provider_manager.ivx import extract_ivx

        with tempfile.TemporaryDirectory() as td:
            ivx = Path(td) / "Changed.ivx"
            _write_ivx(ivx, manifest=_manifest(executable=False))
            inspection = inspect_ivx(ivx)
            _write_ivx(ivx, manifest=_manifest(executable=False, version="2.0"))
            with self.assertRaisesRegex(ValueError, "changed after validation"):
                extract_ivx(inspection, Path(td) / "stage")

    def test_build_helper_creates_deterministic_rooted_ivx(self):
        import importlib.util

        script = Path(__file__).resolve().parents[1] / "scripts" / "provider" / "build_ivx.py"
        spec = importlib.util.spec_from_file_location("invio_build_ivx", script)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "ZohoBooks"
            source.mkdir()
            (source / "provider.json").write_text(json.dumps(_manifest(executable=False)), encoding="utf-8")
            (source / "README.md").write_text("hello", encoding="utf-8")
            first = module.build_ivx(source, root / "one")
            second = module.build_ivx(source, root / "two")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
                self.assertIn("provider.json", names)
                self.assertIn("README.md", names)
                self.assertIn("SHA256SUMS.txt", names)
                self.assertFalse(any(name.startswith("ZohoBooks/") for name in names))
            self.assertTrue(inspect_ivx(first).checksums_verified)

    def test_build_helper_does_not_publish_invalid_final_archive(self):
        import importlib.util

        script = Path(__file__).resolve().parents[1] / "scripts" / "provider" / "build_ivx.py"
        spec = importlib.util.spec_from_file_location("invio_build_ivx_atomic", script)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "Provider"
            source.mkdir()
            manifest = _manifest(provider_id="atomic_provider", executable=False)
            manifest["name"] = "Atomic Provider"
            (source / "provider.json").write_text(json.dumps(manifest), encoding="utf-8")
            output_dir = root / "out"
            expected = output_dir / "Invio_AtomicProvider_Provider_v1.0.0.ivx"
            with patch.object(module, "inspect_ivx", side_effect=ValueError("injected final validation failure")):
                with self.assertRaisesRegex(ValueError, "injected final validation failure"):
                    module.build_ivx(source, output_dir)
            self.assertFalse(expected.exists())
            self.assertFalse(any(output_dir.glob("*.tmp.ivx")))

    def test_build_helper_requires_adapter_when_manifest_declares_runtime(self):
        import importlib.util

        script = Path(__file__).resolve().parents[1] / "scripts" / "provider" / "build_ivx.py"
        spec = importlib.util.spec_from_file_location("invio_build_ivx_missing_adapter", script)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "Provider"
            source.mkdir()
            (source / "provider.json").write_text(json.dumps(_manifest(executable=True)), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing root-level adapter.py"):
                module.build_ivx(source, root / "out")


if __name__ == "__main__":
    unittest.main()
