#!/usr/bin/env python3
"""Sync generated package inputs into one luaskills checkout.
将生成的包输入同步到一个 luaskills 工作副本。
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from catalog_common import load_bundle, repo_root, write_text


def copy_file(source: Path, destination: Path) -> None:
    """Copy one file and create the parent directory first.
    复制一个文件，并在复制前创建父目录。
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def rewrite_lua_packages_for_luaskills(source_text: str) -> str:
    """Rewrite exported package paths so one luaskills checkout can consume them directly.
    重写导出的包路径，使其可被一个 luaskills 工作副本直接消费。
    """

    return source_text.replace(
        "path:dist/luarocks_overrides/windows/",
        "path:scripts/luarocks_overrides/windows/",
    )


def sync_generated_inputs(luaskills_root: Path) -> None:
    """Sync generated compatibility files into one luaskills checkout.
    将生成的兼容文件同步进一个 luaskills 工作副本。
    """

    packages_root = repo_root()
    bundle = load_bundle(packages_root)
    dist_root = packages_root / "dist"

    lua_packages_source = dist_root / "lua_packages.txt"
    if not lua_packages_source.exists():
        raise FileNotFoundError(f"generated lua_packages.txt not found: {lua_packages_source}")

    luaskills_scripts_dir = luaskills_root / "scripts"
    lua_packages_text = lua_packages_source.read_text(encoding="utf-8")
    write_text(
        luaskills_scripts_dir / "lua_packages.txt",
        rewrite_lua_packages_for_luaskills(lua_packages_text),
    )

    override_source_root = dist_root / "luarocks_overrides" / "windows"
    override_destination_root = luaskills_scripts_dir / "luarocks_overrides" / "windows"
    override_destination_root.mkdir(parents=True, exist_ok=True)
    if override_source_root.exists():
        for source_path in sorted(override_source_root.glob("*.rockspec")):
            copy_file(source_path, override_destination_root / source_path.name)

    provenance_payload = {
        "schema_version": 1,
        "source_repository": "LuaSkills/luaskills-packages",
        "bundle_id": bundle["bundle_id"],
        "bundle_version": bundle["bundle_version"],
        "resolved_tag": f"v{bundle['bundle_version']}",
        "generated_files": {
            "lua_packages_txt": str(lua_packages_source.relative_to(packages_root)).replace("\\", "/"),
            "windows_override_directory": str(override_source_root.relative_to(packages_root)).replace("\\", "/")
            if override_source_root.exists()
            else None,
        },
    }
    write_text(
        luaskills_scripts_dir / "lua_packages.generated-from.json",
        json.dumps(provenance_payload, ensure_ascii=False, indent=2) + "\n",
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    解析命令行参数。
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--luaskills-root",
        required=True,
        help="Path to the luaskills repository checkout. / luaskills 仓库工作副本路径。",
    )
    return parser.parse_args()


def main() -> int:
    """Run the sync operation and exit with one process code.
    执行同步操作并返回进程退出码。
    """

    args = parse_args()
    luaskills_root = Path(args.luaskills_root).resolve()
    sync_generated_inputs(luaskills_root)
    print(f"synced generated package inputs into {luaskills_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
