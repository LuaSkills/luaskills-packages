# luaskills-packages

`luaskills-packages` 是 `luaskills` 的包侧配套仓库，用来独立维护 LuaSkills 官方 Lua 运行时包集合、模块目录、帮助元数据、支持目标矩阵和第三方许可证元数据。

## 仓库定位

这个仓库不负责：

- Lua 虚拟机生命周期
- `vulcan.*` API
- FFI / SDK 契约
- runlua / runtime session 核心行为

这些仍属于 `luaskills` 主仓库。

这个仓库负责：

- 官方 Lua 包清单
- package 到 module 的归属关系
- 包帮助元数据
- Windows 等平台的 rockspec override 生成规则
- 官方受支持目标矩阵
- 第三方许可证元数据与导出
- 兼容 `lua_packages.txt` 的导出

## 为什么要拆仓

因为 `luaskills core` 和官方 Lua 包集合不应该强行同版本升级：

1. 核心运行时可能单独修 VM、FFI 或 `vulcan.*`
2. 官方 Lua 包集合可能单独升级某个第三方包
3. 下游宿主可能要 fork 一份 packages 仓库并增加自己的库

拆出来以后，三种场景都更自然。

## 当前受支持平台

当前官方 bundle 只声明支持这 5 个目标：

- `windows-x64`
- `linux-x64`
- `linux-arm64`
- `macos-x64`
- `macos-arm64`

这里不会宣称“支持所有系统”。
因为 LuaSkills 整体运行时本身就存在原生依赖边界，所以 package 仓库也应该只对真实要交付的平台负责。

## 仓库结构

```text
catalog/
  bundle.json
  packages/
  help/packages/
  overrides/windows/
  observed/
  overlays/

templates/
  rockspec/windows/

scripts/
  catalog_common.py
  validate_catalog.py
  export_lua_packages_txt.py
  render_rockspec_overrides.py
  export_platform_support.py
  export_third_party_licenses.py
  fetch_license_texts.py
  scan_runtime_modules.py
```

## 核心设计原则

### 1. 元数据是源码

这里真正的源码是：

- package 元数据
- help 元数据
- override 规则
- 支持目标声明
- license 元数据

不是最终生成出来的 `.rockspec`、`lua_packages.txt` 或许可证汇总文件。

### 2. 产物是生成的

当前仓库会生成多类产物：

- `dist/lua_packages.txt`
- `dist/luarocks_overrides/...`
- `dist/install-manifest.json`
- `dist/help/...`
- `dist/platform-support.json`
- `dist/platform-support.md`
- `dist/THIRD_PARTY_LICENSES.json`
- `dist/THIRD_PARTY_NOTICES.md`
- `dist/licenses/...`

这些文件不应当作为主要维护对象直接手改。

### 3. package catalog 和 runtime scan 分离

单纯扫描 `.lua` / `.dll` 文件并不能可靠说明：

- 哪个 module 属于哪个 package
- 哪些文件只是内部实现
- 哪些 module 才是推荐暴露给 AI 或宿主的公开接口

所以这里明确分成两层：

- **catalog**
  - 人工确认后的 package / module / help / target / license 元数据
- **scan**
  - 对某个实际 runtime 树做观测性扫描

如果需要保留某次官方构建的实际导出结果，可以把观测快照放进 `catalog/observed/`。
但它只用于审计、核对和回归比较，不会覆盖 `catalog/packages/` 里人工确认过的归属信息。

### 4. 不再长期维护大量固定死的 override 副本

过去常见做法是直接把很多 override `.rockspec` 文件签入仓库。

问题是：

- upstream 版本一变，固定副本就开始漂移
- 很难看出哪些是必须改的，哪些只是历史复制
- 维护成本会越来越高

所以这个仓库优先采用两种方式：

1. **参数化模板**
   - 适合 build 逻辑改动较大的包
2. **抓取上游再补丁**
   - 适合只需要小修的包

最终生成的 `.rockspec` 只是输出物，不是事实来源。

## 许可证处理策略

现在每个 package 元数据都包含：

- SPDX 表达式
- 人类可读许可证名称
- 许可证页面 URL
- 上游原始许可证文本 URL（如果可用）

因此可以支持两种合规方式：

1. **仅导出声明清单**
   - 生成第三方许可证 JSON / Markdown 索引
2. **导出并拉取原文**
   - 把上游许可证文本下载到生成目录中

也就是说，这个仓库现在不只是“记录包名”，而是开始具备真正的 license 交付基础。

## 当前官方包集合

当前首版 catalog 覆盖：

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

## fork 方式

推荐的 fork 路线：

1. fork 本仓库
2. 保留官方 `catalog/` 结构
3. 通过新增 package 元数据扩展自己的包
4. 通过 `catalog/overlays/` 写宿主增量信息
5. 跑脚本生成自己的兼容产物

这样做的好处是：

- 你仍然可以同步官方包集合
- 宿主自定义内容不会和官方 catalog 搅在一起

## GitHub Actions 推荐方式

推荐在 CI 中做这些事：

1. 运行 `python scripts/validate_catalog.py`
2. 运行 `python scripts/export_lua_packages_txt.py`
3. 运行 `python scripts/render_rockspec_overrides.py`
4. 运行 `python scripts/export_platform_support.py`
5. 运行 `python scripts/export_runtime_bundle_metadata.py`
6. 运行 `python scripts/export_third_party_licenses.py`
7. 上传 `dist/` 目录作为 artifact

这样：

- 仓库里保留的是规则和元数据
- CI 里生成的是兼容产物

## 常用命令

校验：

```bash
python scripts/validate_catalog.py
```

导出 `lua_packages.txt`：

```bash
python scripts/export_lua_packages_txt.py
```

生成 override rockspec：

```bash
python scripts/render_rockspec_overrides.py
```

导出平台支持矩阵：

```bash
python scripts/export_platform_support.py
```

导出 runtime 安装清单与帮助索引：

```bash
python scripts/export_runtime_bundle_metadata.py
```

导出第三方许可证清单：

```bash
python scripts/export_third_party_licenses.py
```

拉取上游许可证原文：

```bash
python scripts/fetch_license_texts.py
```

扫描一个实际 runtime 的 `lua_packages` 目录：

```bash
python scripts/scan_runtime_modules.py --lua-packages-dir /path/to/runtime/lua_packages --output dist/runtime-scan.json
```

仓库里已经放了一份 `catalog/observed/` 下的官方 Windows 运行时观测样本，用来说明“实际导出了什么模块”，但它不是包归属事实源。

## 发布产物

打 tag 发布时，当前仓库会额外挂出：

- `luaskills-packages-bundle-vX.Y.Z.zip`
- `luaskills-packages-bundle-vX.Y.Z.sha256`
- `lua-deps-{platform}.tar.gz`
- `lua-deps-{platform}.tar.gz.sha256`

其中：

- `bundle` 用于给 `luaskills` runtime 提供包规则、帮助、license 与平台元数据
- `lua-deps` 用于给主仓库和后续 SDK 安装链提供预编译原生依赖资产

## 与主仓库的关系

长期目标是：

1. `luaskills-packages` 负责发布官方包侧 bundle
2. `luaskills` 主仓库只消费 bundle，而不再内嵌所有规则
3. 宿主可以替换官方 bundle，或者叠加自己的 overlay
4. 未来 `lua-help` / runtime help 可以直接读取这里的 catalog，而不是靠扫描或猜测
