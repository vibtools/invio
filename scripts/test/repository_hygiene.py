from __future__ import annotations

import subprocess
from pathlib import Path


class RepositoryHygieneError(RuntimeError):
    """Raised when repository source boundaries are not clean or reproducible."""


_ROOT_TRANSIENT_CHECKSUM = "SHA256SUMS.txt"
_FORBIDDEN_PREFIXES = (
    "project/",
    "build/",
    "dist/",
    "data/runtime/",
    "data/exports/",
)
_FORBIDDEN_COMPONENTS = {"__pycache__", ".pytest_cache"}
_FORBIDDEN_SUFFIXES = (".pyc", ".pyo")


def _run_git(root: Path, args: list[str]) -> bytes:
    root = Path(root).resolve()
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise RepositoryHygieneError(f"Git repository hygiene command failed{suffix}") from exc
    return completed.stdout


def _decode_nul_paths(raw: bytes) -> tuple[str, ...]:
    paths = [part.decode("utf-8", errors="strict") for part in raw.split(b"\0") if part]
    return tuple(sorted(paths))


def repository_candidate_files(root: Path) -> tuple[str, ...]:
    """Return the prospective public worktree candidate set before ``git add``.

    Tracked files and untracked/unignored files are included. Pending deletions are
    omitted because the file is absent from the prospective source worktree.
    Ignored private/runtime/generated material stays outside this candidate set.
    """
    root = Path(root).resolve()
    raw = _run_git(
        root,
        ["ls-files", "-z", "--cached", "--others", "--exclude-standard"],
    )
    paths: list[str] = []
    for relative in _decode_nul_paths(raw):
        if (root / relative).is_file():
            paths.append(relative)
    return tuple(paths)


def committed_source_files(root: Path, ref: str = "HEAD") -> tuple[str, ...]:
    """Return the exact file inventory stored in one committed Git tree."""
    if not ref or ref.startswith("-"):
        raise RepositoryHygieneError("Git source ref must be a non-option ref name.")
    raw = _run_git(root, ["ls-tree", "-r", "--name-only", "-z", ref, "--"])
    return _decode_nul_paths(raw)


def _forbidden_reason(relative: str) -> str | None:
    normalized = relative.replace("\\", "/")
    if normalized == _ROOT_TRANSIENT_CHECKSUM:
        return "repository-root transient SHA256SUMS.txt is not a canonical source artifact"
    if normalized.startswith(_FORBIDDEN_PREFIXES):
        return "private, generated, build, or runtime path is inside the public source candidate set"
    parts = tuple(part for part in normalized.split("/") if part)
    if any(part in _FORBIDDEN_COMPONENTS for part in parts):
        return "generated cache path is inside the public source candidate set"
    if normalized.endswith(_FORBIDDEN_SUFFIXES):
        return "generated Python bytecode is inside the public source candidate set"
    if normalized.startswith("providers/registry/") and normalized != "providers/registry/.gitkeep":
        return "provider registry runtime state is inside the public source candidate set"
    return None


def source_hygiene_failures(root: Path) -> tuple[str, ...]:
    """Return deterministic violations in the prospective public repository source."""
    failures: list[str] = []
    for relative in repository_candidate_files(root):
        reason = _forbidden_reason(relative)
        if reason:
            failures.append(f"{relative}: {reason}")
    return tuple(failures)


def assert_repository_source_hygiene(root: Path) -> int:
    """Fail closed on source-boundary violations and return candidate file count."""
    files = repository_candidate_files(root)
    failures = source_hygiene_failures(root)
    if failures:
        formatted = "\n".join(f"- {failure}" for failure in failures)
        raise RepositoryHygieneError(f"Repository source hygiene audit failed:\n{formatted}")
    return len(files)


def create_source_archive(root: Path, destination: Path, ref: str = "HEAD") -> Path:
    """Export one exact committed Git tree as a ZIP without workspace contamination."""
    if not ref or ref.startswith("-"):
        raise RepositoryHygieneError("Git source ref must be a non-option ref name.")
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "archive",
                "--format=zip",
                f"--output={destination}",
                ref,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        destination.unlink(missing_ok=True)
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise RepositoryHygieneError(f"Unable to export canonical Git source archive{suffix}") from exc
    return destination
