#!/usr/bin/env python3
"""Export supported target matrix artifacts from catalog metadata.
从 catalog 元数据导出受支持目标矩阵产物。
"""

from __future__ import annotations

import json

from catalog_common import load_bundle, load_package_records, load_target_records, repo_root, write_text


def build_json_payload(bundle: dict, package_records: list[dict]) -> dict:
    """Build one machine-readable platform matrix payload.
    构建一份机器可读的平台矩阵载荷。
    """

    return {
        "schema_version": 1,
        "bundle_id": bundle["bundle_id"],
        "bundle_version": bundle["bundle_version"],
        "supported_targets": load_target_records(bundle),
        "packages": [
            {
                "package_name": record["package_name"],
                "rock_name": record["rock_name"],
                "artifact_kind": record["artifact_kind"],
                "platform_matrix": record["platform_matrix"],
            }
            for record in package_records
        ],
    }


def render_cell(entry: dict) -> str:
    """Render one concise Markdown cell for one target entry.
    为单个目标条目渲染简洁的 Markdown 单元格。
    """

    return f"{entry['support_status']} ({entry['build_mode']})"


def build_markdown(bundle: dict, package_records: list[dict]) -> str:
    """Build one human-readable Markdown summary.
    构建一份便于人工阅读的 Markdown 摘要。
    """

    targets = load_target_records(bundle)
    header = [
        "# Platform Support Matrix",
        "",
        "This file is generated from catalog metadata.",
        "此文件由 catalog 元数据自动生成。",
        "",
    ]
    columns = ["Package", "Artifact Kind", *[item["display_name"] for item in targets]]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for record in package_records:
        row = [
            record["package_name"],
            record["artifact_kind"],
            *[render_cell(record["platform_matrix"][item["id"]]) for item in targets],
        ]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(header + lines) + "\n"


def main() -> int:
    """Export platform support JSON and Markdown outputs.
    导出平台支持 JSON 与 Markdown 输出。
    """

    root = repo_root()
    bundle = load_bundle(root)
    package_records = load_package_records(bundle, root)
    json_payload = build_json_payload(bundle, package_records)
    json_path = root / bundle["generated"]["platform_support_json"]
    markdown_path = root / bundle["generated"]["platform_support_markdown"]
    write_text(json_path, json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n")
    write_text(markdown_path, build_markdown(bundle, package_records))
    print(f"wrote {json_path}")
    print(f"wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
