#!/usr/bin/env python3
"""Export third-party license notice artifacts from package metadata.
从 package 元数据导出第三方许可证声明产物。
"""

from __future__ import annotations

import json

from catalog_common import load_bundle, load_package_records, repo_root, write_text


def build_json_payload(bundle: dict, package_records: list[dict]) -> dict:
    """Build one machine-readable third-party license payload.
    构建一份机器可读的第三方许可证载荷。
    """

    return {
        "schema_version": 1,
        "bundle_id": bundle["bundle_id"],
        "bundle_version": bundle["bundle_version"],
        "packages": [
            {
                "package_name": record["package_name"],
                "rock_name": record["rock_name"],
                "license": record["license"],
                "repository": record.get("repository"),
                "homepage": record.get("homepage"),
            }
            for record in package_records
        ],
    }


def build_markdown(package_records: list[dict]) -> str:
    """Build one Markdown notice index from package metadata.
    根据 package 元数据构建 Markdown 声明索引。
    """

    lines = [
        "# Third-Party License Notices",
        "",
        "This file is generated from package metadata.",
        "此文件由 package 元数据自动生成。",
        "",
        "| Package | SPDX | License Name | Policy | License URL | License Text URL |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in package_records:
        license_record = record["license"]
        lines.append(
            "| "
            + " | ".join(
                [
                    record["package_name"],
                    license_record.get("spdx_expression") or "",
                    license_record.get("license_name") or "",
                    license_record.get("license_policy") or "",
                    license_record.get("license_url") or "",
                    license_record.get("license_text_url") or "",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    """Export third-party license JSON and Markdown outputs.
    导出第三方许可证 JSON 与 Markdown 输出。
    """

    root = repo_root()
    bundle = load_bundle(root)
    package_records = load_package_records(bundle, root)
    json_payload = build_json_payload(bundle, package_records)
    json_path = root / bundle["generated"]["third_party_licenses_json"]
    markdown_path = root / bundle["generated"]["third_party_notices_markdown"]
    write_text(json_path, json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n")
    write_text(markdown_path, build_markdown(package_records))
    print(f"wrote {json_path}")
    print(f"wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
