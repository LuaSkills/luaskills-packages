#!/usr/bin/env python3
"""Export one formal luaskills-packages runtime archive from one validated runtime package.
从一个已验证的 runtime 包导出正式的 luaskills-packages runtime 归档。
"""

from __future__ import annotations

import argparse
import json
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any


CORE_LIBRARY_NAMES = {
    "windows-x64": ["luaskills.dll", "libluaskills.dll"],
    "linux-x64": ["libluaskills.so", "luaskills.so"],
    "linux-arm64": ["libluaskills.so", "luaskills.so"],
    "macos-x64": ["libluaskills.dylib", "luaskills.dylib"],
    "macos-arm64": ["libluaskills.dylib", "luaskills.dylib"],
}

LUA_ABI_LIBRARY_PATTERNS = {
    "windows-x64": ["lua51.dll"],
    "linux-x64": ["libluajit-5.1.so*", "libluajit.so*"],
    "linux-arm64": ["libluajit-5.1.so*", "libluajit.so*"],
    "macos-x64": ["libluajit-5.1*.dylib*", "libluajit.dylib*", "libluajit.so*"],
    "macos-arm64": ["libluajit-5.1*.dylib*", "libluajit.dylib*", "libluajit.so*"],
}


def write_json(path: Path, value: Any) -> None:
    """Write one JSON file with stable indentation.
    以稳定缩进格式写入一个 JSON 文件。
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    """Read one JSON file and tolerate UTF-8 BOM produced on Windows.
    读取一个 JSON 文件，并兼容 Windows 侧生成的 UTF-8 BOM。
    """

    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_member_path(member_name: str) -> None:
    """Reject archive members that would escape the extraction root.
    拒绝会逃逸解压根目录的归档成员。
    """

    member_path = Path(member_name)
    if member_path.is_absolute():
        raise ValueError(f"archive member escapes extraction root: {member_name}")
    normalized = member_path.as_posix()
    if normalized.startswith("../") or "/../" in normalized or normalized == "..":
        raise ValueError(f"archive member escapes extraction root: {member_name}")


def extract_runtime_archive(archive_path: Path, destination: Path) -> None:
    """Extract one source runtime archive into one temporary directory.
    将一个源 runtime 归档解压到单个临时目录。
    """

    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            validate_member_path(member.name)
            if member.issym() or member.islnk():
                raise ValueError(f"runtime archive contains unsupported link member: {member.name}")
        archive.extractall(destination, filter="data")


def remove_core_runtime_bits(runtime_root: Path, platform: str) -> list[str]:
    """Remove luaskills core dynamic libraries from one extracted runtime tree.
    从一个已解压 runtime 树中移除 luaskills core 动态库。
    """

    removed: list[str] = []
    libs_root = runtime_root / "libs"
    for name in CORE_LIBRARY_NAMES.get(platform, []):
        candidate = libs_root / name
        if candidate.exists():
            candidate.unlink()
            removed.append(f"libs/{name}")
    return removed


def rewrite_runtime_manifest(runtime_root: Path, platform: str) -> dict[str, Any]:
    """Rewrite the top runtime manifest so it describes the packages-side archive.
    重写顶层 runtime 清单，使其描述 packages 侧归档。
    """

    manifest_path = runtime_root / "resources" / "lua-runtime-manifest.json"
    payload = read_json(manifest_path)
    source_package_name = payload.get("package_name", f"lua-runtime-{platform}")
    payload["package_name"] = f"lua-runtime-packages-{platform}"
    payload["layout"] = "luaskills-runtime-packages-v1"
    payload["generated_from"] = {
        "repository": "LuaSkills/luaskills",
        "package_name": source_package_name,
        "asset_name": f"lua-runtime-{platform}.tar.gz",
    }
    payload["core_runtime_asset_hint"] = {
        "repository": "LuaSkills/luaskills",
        "asset_name": f"luaskills-ffi-sdk-{platform}.tar.gz",
    }
    write_json(manifest_path, payload)
    return payload


def ensure_runtime_packages_manifest(runtime_root: Path, platform: str) -> None:
    """Ensure the extracted runtime tree contains one packages-side manifest file.
    确保已解压的 runtime 目录树包含一个 packages 侧清单文件。
    """

    manifest_path = runtime_root / "resources" / "luaskills-packages-manifest.json"
    if manifest_path.exists():
        return

    packages_root = runtime_root / "resources" / "luaskills-packages"
    install_manifest_path = packages_root / "install-manifest.json"
    install_payload: dict[str, Any] = {}
    if install_manifest_path.exists():
        install_payload = read_json(install_manifest_path)
    source_payload = install_payload.get("source", {}) if isinstance(install_payload.get("source"), dict) else {}
    bundle_version = str(source_payload.get("bundle_version", "0.0.0-local"))
    series = str(source_payload.get("series", "compat"))
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "repository": "LuaSkills/luaskills-packages",
            "bundle_id": str(source_payload.get("bundle_id", "compat-generated")),
            "bundle_version": bundle_version,
            "series": series,
            "resolved_tag": f"v{bundle_version}" if bundle_version and bundle_version != "0.0.0-local" else "",
            "platform": platform,
            "layout": "luaskills-packages-runtime-v1",
            "generation_mode": "runtime-export-normalized",
            "paths": {
                "install_manifest": "resources/luaskills-packages/install-manifest.json",
                "compat_lua_packages_txt": "resources/luaskills-packages/lua_packages.txt",
                "platform_support": "resources/luaskills-packages/platform-support.json",
                "third_party_licenses": "resources/luaskills-packages/THIRD_PARTY_LICENSES.json",
                "third_party_notices": "resources/luaskills-packages/THIRD_PARTY_NOTICES.md",
                "help_index": "resources/luaskills-packages/help/index.json",
                "package_help_root": "resources/luaskills-packages/help/packages",
                "module_help_root": "resources/luaskills-packages/help/modules",
                "license_index": "licenses/luaskills-packages/index.json",
            },
        },
    )


def copy_path(source: Path, destination: Path) -> None:
    """Copy one file or directory into a fresh destination path.
    将单个文件或目录复制到全新的目标路径。
    """

    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def overlay_runtime_packages_metadata(runtime_root: Path, dist_root: Path) -> list[str]:
    """Overlay generated catalog metadata into the runtime-facing packages tree.
    将已生成的 catalog 元数据覆盖进面向运行时的 packages 目录树。
    """

    if not dist_root.exists():
        return []

    copied_paths: list[str] = []
    copy_pairs = [
        ("lua_packages.txt", "resources/luaskills-packages/lua_packages.txt"),
        ("install-manifest.json", "resources/luaskills-packages/install-manifest.json"),
        ("platform-support.json", "resources/luaskills-packages/platform-support.json"),
        ("THIRD_PARTY_LICENSES.json", "resources/luaskills-packages/THIRD_PARTY_LICENSES.json"),
        ("THIRD_PARTY_NOTICES.md", "resources/luaskills-packages/THIRD_PARTY_NOTICES.md"),
        ("help", "resources/luaskills-packages/help"),
        ("licenses", "licenses/luaskills-packages"),
    ]
    for source_name, destination_name in copy_pairs:
        source = dist_root / source_name
        if not source.exists():
            continue
        destination = runtime_root / destination_name
        copy_path(source, destination)
        copied_paths.append(destination_name)
    return copied_paths


def overlay_lua_abi_provider(runtime_root: Path, luajit_root: Path, platform: str) -> list[str]:
    """Copy the platform Lua ABI provider libraries required by Lua C modules.
    复制 Lua C 模块所需的平台 Lua ABI 提供库。
    """

    patterns = LUA_ABI_LIBRARY_PATTERNS.get(platform)
    if not patterns:
        raise ValueError(f"unsupported platform for Lua ABI provider overlay: {platform}")
    if not luajit_root.exists():
        raise FileNotFoundError(f"LuaJIT SDK directory is missing: {luajit_root}")

    libs_dir = runtime_root / "libs"
    libs_dir.mkdir(parents=True, exist_ok=True)
    copied_paths: list[str] = []
    seen_names: set[str] = set()
    for pattern in patterns:
        for source in sorted(luajit_root.glob(pattern)):
            if not source.is_file() or source.name in seen_names:
                continue
            destination = libs_dir / source.name
            shutil.copy2(source, destination)
            copied_paths.append(f"libs/{source.name}")
            seen_names.add(source.name)

    if not copied_paths:
        raise FileNotFoundError(
            f"Lua ABI provider library is missing under {luajit_root} for {platform}"
        )
    return copied_paths


def validate_runtime_relative_path(label: str, relative_path: str) -> None:
    """Validate one manifest path before resolving it under the runtime root.
    在运行时根目录下解析前校验单个清单路径。
    """

    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValueError(f"runtime packages manifest path must be relative: {label}={relative_path}")
    if not candidate.parts:
        raise ValueError(f"runtime packages manifest path must not be empty: {label}")
    if ".." in candidate.parts:
        raise ValueError(f"runtime packages manifest path must not traverse parents: {label}={relative_path}")


def validate_runtime_packages_manifest_targets(runtime_root: Path) -> None:
    """Validate that every path declared by the packages manifest exists.
    校验 packages 清单声明的每一个路径都真实存在。
    """

    manifest_path = runtime_root / "resources" / "luaskills-packages-manifest.json"
    manifest = read_json(manifest_path)
    if manifest.get("schema_version") != 1:
        raise ValueError(f"unsupported luaskills-packages manifest schema_version in {manifest_path}")
    if manifest.get("layout") != "luaskills-packages-runtime-v1":
        raise ValueError(f"unsupported luaskills-packages manifest layout in {manifest_path}")

    paths = manifest.get("paths")
    if not isinstance(paths, dict):
        raise ValueError(f"luaskills-packages manifest paths must be an object: {manifest_path}")

    for label, relative_path in paths.items():
        if not isinstance(relative_path, str):
            raise ValueError(f"luaskills-packages manifest path must be a string: {label}")
        validate_runtime_relative_path(label, relative_path)
        target = runtime_root / relative_path
        if not target.exists():
            raise FileNotFoundError(f"runtime packages manifest target is missing: {relative_path}")


def rewrite_bundled_libs(runtime_root: Path, removed_paths: list[str]) -> None:
    """Drop core runtime library entries from bundled-libs metadata when present.
    在 bundled-libs 元数据存在时移除 core runtime 库条目。
    """

    bundled_path = runtime_root / "resources" / "bundled-libs.json"
    if not bundled_path.exists():
        return
    payload = read_json(bundled_path)
    removed_names = {Path(item).name.lower() for item in removed_paths}
    filtered = []
    for record in payload:
        component = str(record.get("component", "")).lower()
        name = str(record.get("name", "")).lower()
        source_path = str(record.get("source_path", "")).lower()
        if component == "luaskills":
            continue
        if name in removed_names:
            continue
        if any(source_path.endswith(name_hint) for name_hint in removed_names):
            continue
        filtered.append(record)
    write_json(bundled_path, filtered)


def rewrite_license_manifest(runtime_root: Path, platform: str) -> None:
    """Rewrite the runtime license manifest so it excludes the core luaskills component.
    重写 runtime 授权清单，使其排除 core luaskills 组件。
    """

    manifest_path = runtime_root / "licenses" / "manifest.json"
    payload = read_json(manifest_path)
    payload["package_name"] = f"lua-runtime-packages-{platform}"
    payload["components"] = [item for item in payload.get("components", []) if item.get("name") != "luaskills"]
    write_json(manifest_path, payload)


def remove_core_runtime_licenses(runtime_root: Path) -> list[str]:
    """Remove packaged core runtime license directories that belong to luaskills itself.
    移除属于 luaskills 自身的已打包 core runtime 授权目录。
    """

    removed: list[str] = []
    candidate = runtime_root / "licenses" / "luaskills"
    if candidate.exists():
        shutil.rmtree(candidate)
        removed.append("licenses/luaskills")
    return removed


def create_archive_from_runtime(runtime_root: Path, archive_path: Path) -> None:
    """Create one tar.gz archive from the transformed runtime tree.
    从转换后的 runtime 树创建一个 tar.gz 归档。
    """

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as archive:
        for child in sorted(runtime_root.iterdir(), key=lambda item: item.name):
            archive.add(child, arcname=child.name)


def export_runtime_packages_archive(source_archive: Path, platform: str, output_dir: Path) -> Path:
    """Export one formal packages runtime archive.
    导出一个正式的 packages runtime 归档。
    """

    archive_name = f"lua-runtime-packages-{platform}.tar.gz"
    archive_path = output_dir / archive_name

    with tempfile.TemporaryDirectory(prefix="luaskills-runtime-packages-") as temporary_root:
        extracted_root = Path(temporary_root)
        extract_runtime_archive(source_archive, extracted_root)
        dist_root = Path(__file__).resolve().parents[1] / "dist"

        required_paths = [
            extracted_root / "lua_packages",
            extracted_root / "resources" / "lua-runtime-manifest.json",
            extracted_root / "resources" / "luaskills-packages",
            extracted_root / "licenses" / "manifest.json",
        ]
        for required in required_paths:
            if not required.exists():
                raise FileNotFoundError(f"runtime archive is missing required path: {required.relative_to(extracted_root)}")
        ensure_runtime_packages_manifest(extracted_root, platform)
        metadata_overlay_paths = overlay_runtime_packages_metadata(extracted_root, dist_root)
        lua_abi_overlay_paths = overlay_lua_abi_provider(
            extracted_root,
            Path(__file__).resolve().parents[1] / "third_party" / "luajit",
            platform,
        )

        removed_paths = remove_core_runtime_bits(extracted_root, platform)
        removed_paths.extend(remove_core_runtime_licenses(extracted_root))
        rewrite_runtime_manifest(extracted_root, platform)
        rewrite_bundled_libs(extracted_root, removed_paths)
        rewrite_license_manifest(extracted_root, platform)
        validate_runtime_packages_manifest_targets(extracted_root)
        create_archive_from_runtime(extracted_root, archive_path)

    return archive_path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the archive exporter.
    解析归档导出器的命令行参数。
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--source-archive", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> int:
    """Run the archive export workflow and exit with one process status code.
    执行归档导出流程，并返回单个进程状态码。
    """

    args = parse_args()
    archive_path = export_runtime_packages_archive(
        source_archive=Path(args.source_archive).resolve(),
        platform=args.platform,
        output_dir=Path(args.output_dir).resolve(),
    )
    print(f"wrote {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
