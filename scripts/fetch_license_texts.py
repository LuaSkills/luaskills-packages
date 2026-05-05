#!/usr/bin/env python3
"""Fetch upstream license texts declared by package metadata.
拉取 package 元数据声明的上游许可证文本。
"""

from __future__ import annotations

import json
import urllib.request

from catalog_common import load_bundle, load_package_records, repo_root, write_text


def fetch_text(url: str) -> str:
    """Fetch one UTF-8 text resource from one URL.
    从一个 URL 拉取一份 UTF-8 文本资源。
    """

    request = urllib.request.Request(url, headers={"User-Agent": "luaskills-packages-license-fetcher"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def main() -> int:
    """Download license texts for packages that publish one text URL.
    为声明了文本 URL 的 package 下载许可证文本。
    """

    root = repo_root()
    bundle = load_bundle(root)
    package_records = load_package_records(bundle, root)
    out_root = root / bundle["generated"]["license_directory"]
    index_payload = {
        "schema_version": 1,
        "bundle_id": bundle["bundle_id"],
        "bundle_version": bundle["bundle_version"],
        "packages": [],
    }

    for record in package_records:
        license_record = record["license"]
        license_text_url = license_record.get("license_text_url")
        if not license_text_url:
            continue
        content = fetch_text(license_text_url)
        output_path = out_root / record["package_name"] / "LICENSE.txt"
        write_text(output_path, content if content.endswith("\n") else content + "\n")
        index_payload["packages"].append(
            {
                "package_name": record["package_name"],
                "license_text_url": license_text_url,
                "output_path": str(output_path.relative_to(root)).replace("\\", "/"),
            }
        )
        print(f"wrote {output_path}")

    index_path = out_root / "index.json"
    write_text(index_path, json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
