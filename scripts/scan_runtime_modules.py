#!/usr/bin/env python3
"""Scan one realized lua_packages tree into a module inventory JSON.
扫描一个实际生成的 lua_packages 目录并导出模块清单 JSON。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from catalog_common import repo_root, write_text


def module_name_from_share(root: Path, path: Path) -> str:
    """Convert one share/lua path into one Lua module name.
    将一个 share/lua 路径转换成 Lua 模块名。
    """

    relative = path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "init":
        parts = parts[:-1]
    return ".".join(parts)


def module_name_from_lib(root: Path, path: Path) -> str:
    """Convert one lib/lua native artifact path into one module name.
    将一个 lib/lua 原生模块路径转换成 Lua 模块名。
    """

    relative = path.relative_to(root).with_suffix("")
    return ".".join(relative.parts)


def scan_runtime_modules(lua_packages_dir: Path) -> list[dict[str, str]]:
    """Scan the standard share/lua and lib/lua layout.
    扫描标准 share/lua 与 lib/lua 目录布局。
    """

    modules: list[dict[str, str]] = []
    share_dir = lua_packages_dir / "share" / "lua"
    lib_dir = lua_packages_dir / "lib" / "lua"

    if share_dir.exists():
        for path in sorted(share_dir.rglob("*.lua")):
            modules.append(
                {
                    "name": module_name_from_share(share_dir, path),
                    "kind": "lua",
                    "origin_path": path.relative_to(lua_packages_dir).as_posix(),
                }
            )

    if lib_dir.exists():
        patterns = ("*.dll", "*.so", "*.dylib")
        for pattern in patterns:
            for path in sorted(lib_dir.rglob(pattern)):
                modules.append(
                    {
                        "name": module_name_from_lib(lib_dir, path),
                        "kind": "native",
                        "origin_path": path.relative_to(lua_packages_dir).as_posix(),
                    }
                )

    modules.sort(key=lambda item: (item["name"], item["kind"], item["origin_path"]))
    return modules


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    解析命令行参数。
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--lua-packages-dir", required=True, help="Path to one lua_packages root.")
    parser.add_argument("--output", required=True, help="Path to one output JSON file.")
    parser.add_argument(
        "--source-name",
        default="runtime-scan",
        help="Human-readable source label stored in the output payload.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the runtime module scan and emit one JSON file.
    执行运行时模块扫描并输出一个 JSON 文件。
    """

    args = parse_args()
    lua_packages_dir = Path(args.lua_packages_dir).resolve()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root() / output_path

    payload = {
        "schema_version": 1,
        "source_name": args.source_name,
        "lua_packages_dir": str(lua_packages_dir),
        "modules": scan_runtime_modules(lua_packages_dir),
    }
    write_text(output_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
