#!/usr/bin/env python3
"""Export runtime-facing bundle metadata and package help files into dist/.
将面向 runtime 的 bundle 元数据与包帮助文件导出到 dist/。
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from catalog_common import load_bundle, load_package_records, load_target_ids, repo_root, write_text


def write_json(path: Path, value: object) -> None:
    """Write one JSON file with stable indentation.
    以稳定缩进格式写入一个 JSON 文件。
    """

    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def copy_help_directory(bundle: dict, root: Path, dist_root: Path) -> None:
    """Copy curated package help files into the generated runtime-help directory.
    将人工整理的包帮助文件复制到生成后的 runtime-help 目录。
    """

    help_source_root = root / bundle["help_directory"]
    help_output_root = dist_root / "help"
    package_output_root = help_output_root / "packages"
    module_output_root = help_output_root / "modules"

    if help_output_root.exists():
        shutil.rmtree(help_output_root)
    package_output_root.mkdir(parents=True, exist_ok=True)
    module_output_root.mkdir(parents=True, exist_ok=True)

    for source_path in sorted(help_source_root.glob("*.json")):
        shutil.copy2(source_path, package_output_root / source_path.name)


def build_help_index(records: list[dict], bundle: dict) -> dict:
    """Build one runtime-facing help index from package metadata.
    从包元数据构建一个面向 runtime 的帮助索引。
    """

    package_entries = []
    module_entries = []
    for record in records:
        help_file_name = Path(record["help_file"]).name
        package_entries.append(
            {
                "package_name": record["package_name"],
                "rock_name": record.get("rock_name", record["package_name"]),
                "version": record.get("version"),
                "summary": record.get("summary", {}),
                "help_path": f"resources/luaskills-packages/help/packages/{help_file_name}",
            }
        )
        for module in record.get("modules", []):
            module_entries.append(
                {
                    "name": module["name"],
                    "kind": module.get("kind", ""),
                    "visibility": module.get("visibility", ""),
                    "package_name": record["package_name"],
                }
            )
    return {
        "schema_version": 1,
        "bundle_id": bundle["bundle_id"],
        "bundle_version": bundle["bundle_version"],
        "packages": package_entries,
        "modules": module_entries,
    }


def build_install_manifest(records: list[dict], bundle: dict) -> dict:
    """Build one structured install manifest for runtime consumers.
    为 runtime 消费方构建一个结构化安装清单。
    """

    install_packages = []
    for record in records:
        install_packages.append(
            {
                "package_name": record["package_name"],
                "rock_name": record.get("rock_name", record["package_name"]),
                "version": record.get("version"),
                "category": record.get("category"),
                "artifact_kind": record.get("artifact_kind"),
                "summary": record.get("summary", {}),
                "modules": record.get("modules", []),
                "legacy_config": record.get("legacy_config", {}),
                "platform_matrix": record.get("platform_matrix", {}),
                "license": record.get("license", {}),
                "help_path": f"resources/luaskills-packages/help/packages/{Path(record['help_file']).name}",
            }
        )
    return {
        "schema_version": 1,
        "bundle_id": bundle["bundle_id"],
        "bundle_version": bundle["bundle_version"],
        "supported_targets": load_target_ids(bundle),
        "packages": install_packages,
    }


def main() -> int:
    """Export runtime bundle metadata under dist/.
    在 dist/ 下导出 runtime bundle 元数据。
    """

    root = repo_root()
    bundle = load_bundle(root)
    records = load_package_records(bundle, root)
    dist_root = root / "dist"
    dist_root.mkdir(parents=True, exist_ok=True)

    copy_help_directory(bundle, root, dist_root)
    write_json(dist_root / "help" / "index.json", build_help_index(records, bundle))
    write_json(dist_root / "install-manifest.json", build_install_manifest(records, bundle))
    print(f"wrote {dist_root / 'install-manifest.json'}")
    print(f"wrote {dist_root / 'help' / 'index.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
