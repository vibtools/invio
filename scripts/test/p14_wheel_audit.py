from __future__ import annotations

import argparse
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_VERSION = str(tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])
REQUIRED_RESOURCES = {
    "assets/icons/checkmark.svg",
    "assets/icons/search.svg",
    "assets/icons/providers/stripe.png",
    "assets/icons/providers/refrens.png",
    "assets/icons/providers/agiled.png",
    "assets/icons/providers/odoo.png",
    "providers/packages/stripe/provider.json",
    "providers/packages/refrens/provider.json",
    "providers/packages/agiled/provider.json",
    "providers/plugins/odoo/provider.json",
    "providers/plugins/odoo/adapter.py",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    wheel = args.wheel.resolve()

    with zipfile.ZipFile(wheel) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"Wheel integrity failed at {bad}")
        names = set(archive.namelist())
        source_modules = {path.relative_to(ROOT).as_posix() for path in (ROOT / "src").rglob("*.py")}
        missing_modules = sorted(source_modules - names)
        if missing_modules:
            raise SystemExit("Wheel is missing source modules: " + ", ".join(missing_modules))
        missing_resources = sorted(REQUIRED_RESOURCES - names)
        if missing_resources:
            raise SystemExit("Wheel is missing required Invio runtime files: " + ", ".join(missing_resources))

        for relative in REQUIRED_RESOURCES:
            source = (ROOT / relative).read_bytes()
            installed = archive.read(relative)
            if source != installed:
                raise SystemExit(f"Wheel resource bytes differ from source: {relative}")

        dist_info = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(dist_info) != 1:
            raise SystemExit("Wheel has an unexpected dist-info metadata layout.")
        metadata = archive.read(dist_info[0]).decode("utf-8", errors="replace")
        if f"Version: {EXPECTED_VERSION}" not in metadata:
            raise SystemExit(f"Wheel metadata version is not {EXPECTED_VERSION}.")
        entry_name = dist_info[0].rsplit("/", 1)[0] + "/entry_points.txt"
        if entry_name not in names:
            raise SystemExit("Wheel is missing console entrypoint metadata.")
        entrypoints = archive.read(entry_name).decode("utf-8", errors="replace")
        if "invio = src.app:main" not in entrypoints:
            raise SystemExit("Wheel console entrypoint does not target src.app:main.")

    print(
        "P14 wheel content audit PASS "
        f"({len(source_modules)} source modules, {len(REQUIRED_RESOURCES)} exact runtime resources)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
