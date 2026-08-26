from __future__ import annotations

import subprocess
import tokenize
from pathlib import Path


class RepositorySyntaxError(RuntimeError):
    """Raised when one or more repository Python sources are not syntactically valid."""


def repository_python_files(root: Path) -> tuple[Path, ...]:
    """Return auditable Python sources in deterministic repository order.

    The candidate set includes Git-tracked files plus untracked files that are not
    ignored by the repository. This keeps pre-commit verification honest: newly
    added source/test files are audited before ``git add``, while ignored private,
    generated, and bytecode artifacts stay outside the source gate.
    """
    root = Path(root).resolve()
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                "*.py",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = ""
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise RepositorySyntaxError(f"Unable to enumerate repository Python files{suffix}") from exc

    paths: list[Path] = []
    for raw_path in completed.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(raw_path.decode("utf-8", errors="strict"))
        path = root / relative
        # Pending deletions are intentionally absent from the candidate worktree.
        if path.is_file():
            paths.append(path)
    return tuple(sorted(paths, key=lambda path: path.relative_to(root).as_posix()))


def syntax_failures(root: Path) -> tuple[str, ...]:
    """Compile repository Python source text without importing or executing modules."""
    root = Path(root).resolve()
    failures: list[str] = []
    for path in repository_python_files(root):
        relative = path.relative_to(root).as_posix()
        try:
            with tokenize.open(path) as handle:
                source = handle.read()
            compile(source, relative, "exec", dont_inherit=True)
        except (SyntaxError, UnicodeError) as exc:
            if isinstance(exc, SyntaxError):
                location = f"line {exc.lineno}" if exc.lineno else "unknown line"
                message = exc.msg or exc.__class__.__name__
            else:
                location = "source decoding"
                message = str(exc)
            failures.append(f"{relative}: {message} ({location})")
    return tuple(failures)


def assert_repository_python_syntax(root: Path) -> int:
    """Fail closed on invalid repository Python and return the number checked."""
    files = repository_python_files(root)
    failures = syntax_failures(root)
    if failures:
        formatted = "\n".join(f"- {failure}" for failure in failures)
        raise RepositorySyntaxError(f"Repository Python syntax audit failed:\n{formatted}")
    return len(files)


# Compatibility aliases retained for the already-issued Phase-01 delta helper/tests.
def tracked_python_files(root: Path) -> tuple[Path, ...]:
    return repository_python_files(root)


def assert_tracked_python_syntax(root: Path) -> int:
    return assert_repository_python_syntax(root)
