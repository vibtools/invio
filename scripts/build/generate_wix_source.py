from __future__ import annotations

import argparse
import hashlib
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from version_info import current_release_version

WIX_NAMESPACE = "http://wixtoolset.org/schemas/v4/wxs"
UPGRADE_CODE = "B3BBE54F-1C68-4A68-A11D-5BA6CF6C4B31"
COMPONENT_NAMESPACE = uuid.UUID("79af0c4d-6b0e-4e0e-9f83-14eaf194d537")

ET.register_namespace("", WIX_NAMESPACE)


def _q(tag: str) -> str:
    return f"{{{WIX_NAMESPACE}}}{tag}"


def _id(prefix: str, value: str) -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def generate_wix_source(dist: Path, output: Path) -> Path:
    dist = dist.resolve()
    output = output.resolve()
    exe = dist / "Invio.exe"
    if not dist.is_dir() or not exe.is_file():
        raise FileNotFoundError("WiX source generation requires a prepared OneDir folder containing Invio.exe.")

    release = current_release_version()
    root = ET.Element(_q("Wix"))
    package = ET.SubElement(
        root,
        _q("Package"),
        {
            "Name": "Invio",
            "Manufacturer": "Vib Tools",
            "Language": "1033",
            "Version": release.msi_version,
            "UpgradeCode": UPGRADE_CODE,
            "ProductCode": "*",
            "Compressed": "yes",
            # Per-user installation is deliberate: Invio's frozen P13 provider
            # registry is writable runtime state located under application_root.
            # Installing under LocalAppData preserves that workflow without UAC.
            "Scope": "perUser",
        },
    )
    ET.SubElement(package, _q("MajorUpgrade"), {"DowngradeErrorMessage": "A newer version of Invio is already installed."})
    ET.SubElement(package, _q("MediaTemplate"), {"EmbedCab": "yes"})
    ET.SubElement(package, _q("Property"), {"Id": "ARPCOMMENTS", "Value": f"Invio {release.application} by Vib Tools"})

    feature = ET.SubElement(package, _q("Feature"), {"Id": "Main", "Title": "Invio", "Level": "1"})

    standard = ET.SubElement(root, _q("Fragment"))
    local = ET.SubElement(standard, _q("StandardDirectory"), {"Id": "LocalAppDataFolder"})
    company_dir = ET.SubElement(local, _q("Directory"), {"Id": "VibToolsFolder", "Name": "Vib Tools"})
    install_dir = ET.SubElement(company_dir, _q("Directory"), {"Id": "INSTALLFOLDER", "Name": "Invio"})

    directory_nodes: dict[Path, ET.Element] = {Path("."): install_dir}
    for directory in sorted((path for path in dist.rglob("*") if path.is_dir()), key=lambda p: (len(p.relative_to(dist).parts), p.as_posix().casefold())):
        relative = directory.relative_to(dist)
        parent_rel = relative.parent if relative.parent != Path("") else Path(".")
        parent = directory_nodes[parent_rel]
        node = ET.SubElement(parent, _q("Directory"), {"Id": _id("D_", relative.as_posix()), "Name": directory.name})
        directory_nodes[relative] = node

    files = sorted((path for path in dist.rglob("*") if path.is_file()), key=lambda p: p.relative_to(dist).as_posix().casefold())
    if not files:
        raise ValueError("Prepared OneDir folder is empty.")

    for path in files:
        relative = path.relative_to(dist)
        parent_rel = relative.parent if relative.parent != Path("") else Path(".")
        parent = directory_nodes[parent_rel]
        rel_key = relative.as_posix()
        component_id = _id("C_", rel_key)
        component_guid = "{" + str(uuid.uuid5(COMPONENT_NAMESPACE, rel_key)).upper() + "}"
        component = ET.SubElement(parent, _q("Component"), {"Id": component_id, "Guid": component_guid})
        ET.SubElement(
            component,
            _q("File"),
            {
                "Id": _id("F_", rel_key),
                "Source": str(path),
                "KeyPath": "yes",
            },
        )
        ET.SubElement(feature, _q("ComponentRef"), {"Id": component_id})

    output.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a WiX v4/v6-compatible per-user MSI source from Invio OneDir.")
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = generate_wix_source(args.dist, args.output)
    print(f"Generated WiX source: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
