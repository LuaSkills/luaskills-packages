#!/usr/bin/env python3
"""Shared helpers for luaskills-packages catalog scripts.
luaskills-packages catalog 脚本共享辅助函数。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def repo_root() -> Path:
    """Return the repository root inferred from this script location.
    根据当前脚本位置推导仓库根目录。
    """

    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> Any:
    """Load one UTF-8 JSON file.
    读取一个 UTF-8 JSON 文件。
    """

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def bundle_file(root: Path | None = None) -> Path:
    """Return the canonical bundle metadata file path.
    返回规范的 bundle 元数据文件路径。
    """

    effective_root = root or repo_root()
    return effective_root / "catalog" / "bundle.json"


def load_bundle(root: Path | None = None) -> dict[str, Any]:
    """Load bundle metadata from the repository root.
    从仓库根目录加载 bundle 元数据。
    """

    return load_json(bundle_file(root))


def load_target_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Return bundle-declared supported target records.
    返回 bundle 声明的受支持目标记录。
    """

    return list(bundle.get("supported_targets", []))


def load_target_ids(bundle: dict[str, Any]) -> list[str]:
    """Return bundle-declared supported target identifiers.
    返回 bundle 声明的受支持目标标识列表。
    """

    return [record["id"] for record in load_target_records(bundle)]


def package_directory(bundle: dict[str, Any], root: Path | None = None) -> Path:
    """Resolve the package metadata directory.
    解析 package 元数据目录。
    """

    effective_root = root or repo_root()
    return effective_root / bundle["package_directory"]


def load_package_map(bundle: dict[str, Any], root: Path | None = None) -> dict[str, dict[str, Any]]:
    """Load every package JSON file into one name-keyed map.
    将全部 package JSON 文件加载成以名称为键的映射。
    """

    package_dir = package_directory(bundle, root)
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(package_dir.glob("*.json")):
        package_record = load_json(path)
        package_record["_path"] = path
        result[package_record["package_name"]] = package_record
    return result


def load_package_records(bundle: dict[str, Any], root: Path | None = None) -> list[dict[str, Any]]:
    """Load package records in bundle-declared order.
    按 bundle 声明顺序加载 package 记录。
    """

    package_map = load_package_map(bundle, root)
    ordered_names = bundle.get("package_order", [])
    records: list[dict[str, Any]] = []
    for name in ordered_names:
        if name in package_map:
            records.append(package_map.pop(name))
    for name in sorted(package_map):
        records.append(package_map[name])
    return records


def render_placeholders(text: str, values: dict[str, Any]) -> str:
    """Render simple `{{name}}` placeholders with scalar values.
    使用标量值渲染简单的 `{{name}}` 占位符。
    """

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"missing placeholder value: {key}")
        value = values[key]
        return "" if value is None else str(value)

    return PLACEHOLDER_PATTERN.sub(replace, text)


def build_template_context(
    package_record: dict[str, Any], extra_values: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build one flat template context from package and rule values.
    从 package 与规则值构建扁平模板上下文。
    """

    context = {
        "package_name": package_record["package_name"],
        "rock_name": package_record.get("rock_name"),
        "version": package_record.get("version"),
        "category": package_record.get("category"),
    }
    if extra_values:
        context.update(extra_values)
    return context


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text and create parent directories first.
    先创建父目录，再写入 UTF-8 文本。
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
