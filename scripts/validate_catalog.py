#!/usr/bin/env python3
"""Validate luaskills-packages catalog metadata.
校验 luaskills-packages catalog 元数据。
"""

from __future__ import annotations

import sys
from pathlib import Path

from catalog_common import load_bundle, load_package_records, load_target_records, repo_root


SUPPORTED_TARGET_IDS = {
    "windows-x64",
    "linux-x64",
    "linux-arm64",
    "macos-x64",
    "macos-arm64",
}
SUPPORTED_ARTIFACT_KINDS = {"lua-only", "native", "hybrid"}
SUPPORTED_LICENSE_POLICIES = {"link-only", "link-or-fetch", "embedded"}
SUPPORTED_SUPPORT_STATES = {"supported", "unsupported", "planned"}
SUPPORTED_BUILD_MODES = {
    "pure-lua",
    "upstream-luarocks",
    "generated-override",
    "fetch-and-patch",
}


def validate_bundle(root: Path, errors: list[str]) -> dict:
    """Load and validate bundle-level metadata.
    加载并校验 bundle 级元数据。
    """

    bundle = load_bundle(root)
    if bundle.get("schema_version") != 1:
        errors.append("bundle schema_version must be 1")

    package_order = bundle.get("package_order", [])
    if len(package_order) != len(set(package_order)):
        errors.append("bundle package_order contains duplicates")

    category_order = bundle.get("category_order", [])
    if len(category_order) != len(set(category_order)):
        errors.append("bundle category_order contains duplicates")

    target_records = load_target_records(bundle)
    if not isinstance(target_records, list) or not target_records:
        errors.append("bundle supported_targets must be a non-empty list")
    else:
        target_ids = [record.get("id") for record in target_records]
        if len(target_ids) != len(set(target_ids)):
            errors.append("bundle supported_targets contains duplicate ids")
        if set(target_ids) != SUPPORTED_TARGET_IDS:
            errors.append(
                "bundle supported_targets must exactly match: "
                + ", ".join(sorted(SUPPORTED_TARGET_IDS))
            )
        for record in target_records:
            if not record.get("os"):
                errors.append(f"target {record.get('id')}: os is required")
            if not record.get("arch"):
                errors.append(f"target {record.get('id')}: arch is required")
            if not record.get("display_name"):
                errors.append(f"target {record.get('id')}: display_name is required")

    return bundle


def validate_package_records(root: Path, bundle: dict, errors: list[str]) -> None:
    """Validate package records and cross-file references.
    校验 package 记录与跨文件引用。
    """

    records = load_package_records(bundle, root)
    bundle_targets = [record["id"] for record in load_target_records(bundle)]
    seen_modules: dict[str, str] = {}
    for record in records:
        package_name = record["package_name"]
        if record.get("schema_version") != 1:
            errors.append(f"{package_name}: schema_version must be 1")

        artifact_kind = record.get("artifact_kind")
        if artifact_kind not in SUPPORTED_ARTIFACT_KINDS:
            errors.append(
                f"{package_name}: artifact_kind must be one of {sorted(SUPPORTED_ARTIFACT_KINDS)}"
            )

        help_file = record.get("help_file")
        if not help_file:
            errors.append(f"{package_name}: help_file is required")
        else:
            help_path = root / help_file
            if not help_path.exists():
                errors.append(f"{package_name}: help_file does not exist: {help_file}")

        modules = record.get("modules", [])
        if not isinstance(modules, list):
            errors.append(f"{package_name}: modules must be a list")
        else:
            for module in modules:
                module_name = module.get("name")
                if not module_name:
                    errors.append(f"{package_name}: module entry without name")
                    continue
                owner = seen_modules.get(module_name)
                if owner and owner != package_name:
                    errors.append(
                        f"module {module_name} is declared by both {owner} and {package_name}"
                    )
                else:
                    seen_modules[module_name] = package_name

        legacy_config = record.get("legacy_config", {})
        for key in ("install", "args", "env", "dependencies", "depvars"):
            value = legacy_config.get(key, [])
            if not isinstance(value, list):
                errors.append(f"{package_name}: legacy_config.{key} must be a list")

        override_rules = record.get("override_rules", {})
        if not isinstance(override_rules, dict):
            errors.append(f"{package_name}: override_rules must be an object")
        else:
            for os_name, relative_path in override_rules.items():
                override_path = root / relative_path
                if not override_path.exists():
                    errors.append(
                        f"{package_name}: override rule for {os_name} does not exist: {relative_path}"
                    )

        license_record = record.get("license")
        if not isinstance(license_record, dict):
            errors.append(f"{package_name}: license must be an object")
        else:
            if not license_record.get("license_name"):
                errors.append(f"{package_name}: license.license_name is required")
            if not license_record.get("license_url"):
                errors.append(f"{package_name}: license.license_url is required")
            policy = license_record.get("license_policy")
            if policy not in SUPPORTED_LICENSE_POLICIES:
                errors.append(
                    f"{package_name}: license.license_policy must be one of {sorted(SUPPORTED_LICENSE_POLICIES)}"
                )
            if policy == "link-or-fetch" and not license_record.get("license_text_url"):
                errors.append(f"{package_name}: license_text_url is required for link-or-fetch policy")

        platform_matrix = record.get("platform_matrix")
        if not isinstance(platform_matrix, dict):
            errors.append(f"{package_name}: platform_matrix must be an object")
        else:
            if set(platform_matrix) != set(bundle_targets):
                errors.append(
                    f"{package_name}: platform_matrix must declare exactly these targets: {bundle_targets}"
                )
            for target_id, target_entry in platform_matrix.items():
                if not isinstance(target_entry, dict):
                    errors.append(f"{package_name}: platform_matrix.{target_id} must be an object")
                    continue
                support_status = target_entry.get("support_status")
                if support_status not in SUPPORTED_SUPPORT_STATES:
                    errors.append(
                        f"{package_name}: platform_matrix.{target_id}.support_status must be one of {sorted(SUPPORTED_SUPPORT_STATES)}"
                    )
                build_mode = target_entry.get("build_mode")
                if support_status == "supported" and build_mode not in SUPPORTED_BUILD_MODES:
                    errors.append(
                        f"{package_name}: platform_matrix.{target_id}.build_mode must be one of {sorted(SUPPORTED_BUILD_MODES)}"
                    )
                if build_mode == "generated-override":
                    target_os = target_id.split("-", 1)[0]
                    if target_os not in override_rules:
                        errors.append(
                            f"{package_name}: platform_matrix.{target_id} uses generated-override but override_rules.{target_os} is missing"
                        )


def validate_overlay_examples(root: Path, errors: list[str]) -> None:
    """Validate checked-in overlay examples.
    校验仓库内提交的 overlay 示例。
    """

    overlay_dir = root / "catalog" / "overlays"
    for path in sorted(overlay_dir.glob("*.json")):
        if not path.exists():
            continue
        try:
            import json

            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:  # pragma: no cover - diagnostic branch
            errors.append(f"{path}: failed to parse overlay JSON: {error}")
            continue
        if payload.get("schema_version") != 1:
            errors.append(f"{path}: schema_version must be 1")
        if not payload.get("overlay_name"):
            errors.append(f"{path}: overlay_name is required")


def main() -> int:
    """Run validation and return one process exit code.
    执行校验并返回进程退出码。
    """

    root = repo_root()
    errors: list[str] = []
    bundle = validate_bundle(root, errors)
    validate_package_records(root, bundle, errors)
    validate_overlay_examples(root, errors)

    if errors:
        print("catalog validation failed")
        for item in errors:
            print(f"- {item}")
        return 1

    package_count = len(load_package_records(bundle, root))
    print(f"catalog validation succeeded ({package_count} packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
