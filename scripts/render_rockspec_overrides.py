#!/usr/bin/env python3
"""Generate LuaRocks override sources from metadata rules.
根据元数据规则生成 LuaRocks override 源文件。
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

from catalog_common import (
    build_template_context,
    load_bundle,
    load_json,
    load_package_records,
    render_placeholders,
    repo_root,
    write_text,
)


def render_template_rule(root: Path, package_record: dict, rule: dict) -> str:
    """Render one override from a local template file.
    从本地模板文件渲染一个 override。
    """

    template_path = root / rule["template_file"]
    template_text = template_path.read_text(encoding="utf-8")
    context = build_template_context(package_record, rule.get("variables", {}))
    return render_placeholders(template_text, context)


def render_fetch_and_patch_rule(package_record: dict, rule: dict) -> str:
    """Fetch one upstream rockspec and apply ordered text replacements.
    拉取一个上游 rockspec 并按顺序应用文本替换。
    """

    upstream = rule["upstream"]
    with urllib.request.urlopen(upstream["url"], timeout=30) as response:
        text = response.read().decode("utf-8")
    context = build_template_context(package_record, rule.get("variables", {}))
    for replacement in rule.get("replacements", []):
        old = render_placeholders(replacement["old"], context)
        new = render_placeholders(replacement["new"], context)
        count = replacement.get("count", -1)
        if count == -1:
            text = text.replace(old, new)
        else:
            text = text.replace(old, new, count)
    prepend = rule.get("prepend")
    if prepend:
        text = render_placeholders(prepend, context) + text
    append = rule.get("append")
    if append:
        text = text + render_placeholders(append, context)
    return text


def main() -> int:
    """Render every declared override rule into the dist directory.
    将所有声明过的 override 规则渲染到 dist 目录。
    """

    root = repo_root()
    bundle = load_bundle(root)
    out_root = root / bundle["generated"]["luarocks_override_directory"]
    package_records = load_package_records(bundle, root)
    generated_files: list[Path] = []

    for package_record in package_records:
        for os_name, relative_rule_path in package_record.get("override_rules", {}).items():
            rule_path = root / relative_rule_path
            rule = load_json(rule_path)
            context = build_template_context(package_record, rule.get("variables", {}))
            output_name = render_placeholders(rule["output_name"], context)
            if rule["strategy"] == "template":
                rendered = render_template_rule(root, package_record, rule)
            elif rule["strategy"] == "fetch_and_patch":
                rendered = render_fetch_and_patch_rule(package_record, rule)
            else:
                raise ValueError(f"unsupported rule strategy: {rule['strategy']}")

            output_path = out_root / os_name / output_name
            write_text(output_path, rendered.rstrip() + "\n")
            generated_files.append(output_path)

    for path in generated_files:
        print(f"wrote {path}")
    print(f"generated {len(generated_files)} override file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
