# luaskills-packages

Official Lua package bundles, module catalogs, generated LuaRocks override sources, platform support metadata, and license metadata for LuaSkills runtimes.

中文说明见 [README.zh-CN.md](./README.zh-CN.md)。

## What This Repository Is

`luaskills-packages` is the package-side companion repository for [`luaskills`](https://github.com/LuaSkills/luaskills).

It exists to separate two concerns that should not be versioned as one unit:

1. **LuaSkills core runtime**
   - VM lifecycle
   - `vulcan.*` APIs
   - FFI and SDK contracts
   - runtime session and runlua behavior
2. **Official Lua runtime package bundle**
   - third-party Lua packages
   - package-to-module catalogs
   - generated LuaRocks compatibility files
   - package help metadata
   - platform support declarations
   - third-party license metadata

The core runtime can evolve independently from the official package bundle, and forks can replace or extend the package side without forking the entire runtime core.

## What This Repository Is Not

- It is **not** the LuaSkills core runtime repository.
- It is **not** a direct copy of a shipped `lua_packages/` tree.
- It is **not** a place to check in opaque generated rockspecs as the source of truth.

Instead, this repository stores:

- package rules
- module ownership catalogs
- package help metadata
- override generation rules
- supported-target metadata
- third-party license metadata
- scripts that export compatibility artifacts

## Design Goals

1. **Independent release cadence**
   - package metadata and package bundle updates should not require a core runtime release
2. **Declarative source of truth**
   - package rules, override rules, target support, and license metadata are authored as metadata
3. **Generated compatibility artifacts**
   - files such as `lua_packages.txt`, Windows override rockspecs, target matrices, and license manifests are generated outputs
4. **Fork-friendly extension**
   - downstream users can fork this repository and add host-specific packages or overlays
5. **AI-readable metadata**
   - package help and module ownership data are stored as explicit files rather than inferred only from filesystem scans
6. **Release-target discipline**
   - the official bundle targets only the supported runtime platforms instead of pretending to support every operating system
7. **License traceability**
   - each package carries explicit license metadata and can export notice artifacts or fetched license texts

## Supported Runtime Targets

The official package bundle is currently scoped to these runtime targets only:

- `windows-x64`
- `linux-x64`
- `linux-arm64`
- `macos-x64`
- `macos-arm64`

This repository does **not** claim support for every operating system or architecture.
That constraint is intentional, because the wider LuaSkills runtime also has native dependency boundaries.

## Repository Layout

```text
catalog/
  bundle.json                     # Bundle-level metadata and ordering
  packages/                       # One JSON file per official package
  help/packages/                  # One JSON help file per official package
  overrides/windows/              # Override generation rules for Windows-specific rockspecs
  observed/                       # Observed runtime snapshots from one realized bundle build
  overlays/                       # Example host extension overlays

templates/
  rockspec/windows/               # Parameterized rockspec templates

scripts/
  catalog_common.py               # Shared catalog loader helpers
  validate_catalog.py             # Structural validation
  export_lua_packages_txt.py      # Generate compatibility lua_packages.txt
  render_rockspec_overrides.py    # Generate override rockspec outputs
  export_platform_support.py      # Export supported target matrix artifacts
  export_third_party_licenses.py  # Export third-party notice artifacts
  fetch_license_texts.py          # Download upstream license texts into generated outputs
  scan_runtime_modules.py         # Scan one realized runtime tree into an observed module inventory

.github/workflows/
  validate.yml                    # CI validation and artifact generation
```

## Source Of Truth Model

This repository uses six layers of package knowledge:

1. **Bundle metadata**
   - package order
   - category order
   - output locations
   - supported targets
2. **Package metadata**
   - package identity
   - public modules
   - legacy compatibility export fields
   - linked help file
   - per-target build mode
   - per-package license metadata
3. **Override generation rules**
   - how a Windows rockspec override is rendered or patched
4. **Observed runtime snapshots**
   - what one realized bundle build actually emitted
5. **Host overlays**
   - optional downstream additions, removals, or ownership adjustments
6. **Generated artifacts**
   - compatibility exports derived from the catalog rather than checked in as the primary source

This means LuaSkills consumers no longer need to guess package structure by scanning random `.lua` files alone.

## Why Generated Rockspecs Instead Of Checked-in Override Sources

Historically, projects often end up checking in many custom `.rockspec` files directly.
That approach becomes brittle when upstream package versions move, because the checked-in copy silently drifts away from upstream.

This repository prefers:

- **parameterized templates** when the override rewrites substantial build logic
- **fetch-and-patch rules** when the upstream rockspec is mostly correct and only needs small changes

Generated `.rockspec` files are outputs, not the canonical source of truth.

## License Handling Policy

This repository tracks license metadata per package, including:

- SPDX expression
- human-readable license name
- canonical license page URL
- raw license text URL when the upstream project publishes one

That makes two workflows possible:

1. **link-first compliance**
   - export a machine-readable and Markdown notice manifest
2. **fetch-and-archive compliance**
   - download upstream license texts into a generated output directory

The repository keeps license metadata in source control, while fetched license texts remain generated outputs.

## Current Official Bundle Scope

The initial official bundle metadata covers the package set currently shipped by LuaSkills:

- `lua-cjson`
- `luafilesystem`
- `luasocket`
- `luasec`
- `lua-curl`
- `lrexlib-pcre2`
- `luaossl`
- `lyaml`
- `lua-toml`
- `serpent`
- `lua-zlib`

## Package Catalog Vs Runtime Scan

This repository deliberately distinguishes between:

- **package catalog**
  - curated ownership and public module metadata
- **runtime scan**
  - observed files from one built runtime tree

An observed runtime snapshot can be checked in under `catalog/observed/` when the official bundle build needs an auditable record of what was actually emitted by one platform build.
That snapshot is useful for validation and review, but it does not override curated ownership metadata in `catalog/packages/`.

The runtime scan is useful, but it is not enough by itself.
For example, one package may expose many Lua modules, and not every discovered file should be treated as a standalone first-class library.

That is why this repository keeps package metadata separate from runtime scanning.

## How To Fork And Customize

Forking is expected.

Typical downstream customization patterns:

1. Add a new package JSON file under `catalog/packages/`
2. Add or update a package help file under `catalog/help/packages/`
3. Add override generation rules if one platform needs custom build behavior
4. Add a host overlay under `catalog/overlays/`
5. Regenerate compatibility artifacts

Recommended downstream policy:

- keep official package metadata in the same schema
- add host-specific modules through overlays rather than editing the official bundle in-place when possible

## Generated Outputs

The repository can generate several important outputs:

1. **`dist/lua_packages.txt`**
   - compatibility export for existing LuaSkills-side package installers
2. **`dist/luarocks_overrides/...`**
   - generated platform-specific override rockspecs
3. **`dist/install-manifest.json`**
   - structured package/install metadata for runtime consumers
4. **`dist/help/...`**
   - runtime-facing package help index and curated package help files
5. **`dist/platform-support.json` and `dist/platform-support.md`**
   - generated target support matrix for the official bundle
6. **`dist/THIRD_PARTY_LICENSES.json` and `dist/THIRD_PARTY_NOTICES.md`**
   - generated third-party notice manifests
7. **`dist/licenses/...`**
   - optionally fetched upstream license texts

These outputs are intentionally ignored by Git and should be produced in CI or local release workflows.

## Local Commands

Use Python 3.11+ or newer.

Validate metadata:

```bash
python scripts/validate_catalog.py
```

Generate compatibility `lua_packages.txt`:

```bash
python scripts/export_lua_packages_txt.py
```

Generate override rockspec outputs:

```bash
python scripts/render_rockspec_overrides.py
```

Export the supported target matrix:

```bash
python scripts/export_platform_support.py
```

Export runtime-facing install/help metadata:

```bash
python scripts/export_runtime_bundle_metadata.py
```

Export third-party notice manifests:

```bash
python scripts/export_third_party_licenses.py
```

Fetch upstream license texts into generated outputs:

```bash
python scripts/fetch_license_texts.py
```

Scan a realized runtime tree into one module inventory JSON:

```bash
python scripts/scan_runtime_modules.py --lua-packages-dir /path/to/runtime/lua_packages --output dist/runtime-scan.json
```

An example observed snapshot is checked in under `catalog/observed/` to document the current official Windows runtime export surface without turning that snapshot into the canonical ownership source.

## GitHub Actions Workflow

This repository is designed to work cleanly with GitHub Actions:

- validate the catalog on every push and pull request
- generate compatibility artifacts
- export platform support and third-party notice artifacts
- export runtime-facing install manifests and package help
- upload the generated `dist/` directory as a CI artifact

Tagged releases also publish:

- `luaskills-packages-bundle-vX.Y.Z.zip`
- `luaskills-packages-bundle-vX.Y.Z.sha256`
- `lua-deps-{platform}.tar.gz`
- `lua-deps-{platform}.tar.gz.sha256`

That model keeps the repository human-authored while still making generated outputs easy to inspect in CI.

## How LuaSkills Core Should Consume This Repository

The long-term intended flow is:

1. `luaskills-packages` publishes bundle metadata and generated artifacts
2. `luaskills` consumes the official package bundle as an external component
3. hosts may replace or extend the bundle with their own overlay metadata
4. future `lua-help` or runtime-help surfaces can read bundle metadata instead of guessing package/module support

## Chinese Summary

### 这个仓库的用途

这个仓库专门承载 LuaSkills 官方 Lua 包集合相关的内容，包括：

- 包规则
- 模块归属目录
- 包帮助元数据
- LuaRocks override 生成规则
- 支持目标矩阵
- 第三方许可证元数据与导出脚本
- 兼容产物导出脚本

### 为什么要独立

这样做可以把：

- `luaskills` 核心运行时升级
- 官方 Lua 包集合升级

拆成两条独立节奏，避免两边强耦合。

### 受支持平台

当前官方 bundle 只面向以下目标：

- `windows-x64`
- `linux-x64`
- `linux-arm64`
- `macos-x64`
- `macos-arm64`

这里不会假装支持一切系统，而是只声明 LuaSkills 官方运行时真正要覆盖的目标集合。

### fork 的推荐方式

如果你有宿主自己的 Lua 包：

1. fork 本仓库
2. 新增自己的 package 元数据
3. 通过 overlay 增量补充宿主模块
4. 生成自己的 bundle 产物

### CI 的推荐方式

GitHub Actions 里推荐做这些事：

1. 校验 catalog
2. 生成 `lua_packages.txt`
3. 生成 override rockspec
4. 导出平台支持矩阵与第三方许可证清单
5. 上传 artifact
