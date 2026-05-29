"""Build a minimal LuaJIT SDK through a tiny Rust crate.
通过一个极小 Rust crate 构建最小 LuaJIT SDK。
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path


ARTIFACT_PATTERNS = [
    "lua51.dll",
    "lua51.lib",
    "libluajit-5.1.so*",
    "libluajit-5.1.a",
    "libluajit-5.1*.dylib*",
    "libluajit.so*",
    "libluajit.a",
    "libluajit.dylib*",
    "luajit.exe",
    "luajit",
]

RUNTIME_LIBRARY_PATTERNS = {
    "windows-x64": ["lua51.dll"],
    "linux-x64": ["libluajit-5.1.so*", "libluajit.so*"],
    "linux-arm64": ["libluajit-5.1.so*", "libluajit.so*"],
    "macos-x64": ["libluajit-5.1*.dylib*", "libluajit.dylib*", "libluajit.so*"],
    "macos-arm64": ["libluajit-5.1*.dylib*", "libluajit.dylib*", "libluajit.so*"],
}


def repo_root() -> Path:
    """Return the repository root based on this script location.
    根据当前脚本位置返回仓库根目录。
    """

    return Path(__file__).resolve().parents[1]


def resolve_luaskills_root(root: Path, explicit_root: str) -> Path:
    """Resolve the luaskills checkout used as the mlua dependency source.
    解析作为 mlua 依赖来源的 luaskills 工作副本。
    """

    candidates = []
    if explicit_root:
        candidates.append(Path(explicit_root))
    candidates.extend(
        [
            root / "luaskills",
            root.parent / "vulcan-luaskills",
            root.parent / "luaskills",
        ]
    )
    for candidate in candidates:
        resolved = candidate.resolve()
        if (resolved / "Cargo.toml").exists():
            return resolved
    raise FileNotFoundError("luaskills Cargo.toml was not found; pass --luaskills-root")


def read_mlua_dependency_line(luaskills_root: Path) -> str:
    """Read the mlua dependency declaration from the luaskills Cargo manifest.
    从 luaskills Cargo 清单读取 mlua 依赖声明。
    """

    cargo_toml = luaskills_root / "Cargo.toml"
    for raw_line in cargo_toml.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("mlua "):
            return stripped
        if stripped.startswith("mlua="):
            return stripped
    raise RuntimeError(f"mlua dependency declaration was not found in {cargo_toml}")


def write_builder_crate(builder_root: Path, mlua_dependency_line: str) -> Path:
    """Write a temporary minimal Rust crate that reuses the luaskills mlua dependency line.
    写入一个复用 luaskills mlua 依赖行的临时最小 Rust crate。
    """

    if builder_root.exists():
        shutil.rmtree(builder_root)
    source_dir = builder_root / "src"
    source_dir.mkdir(parents=True, exist_ok=True)
    (builder_root / "Cargo.toml").write_text(
        textwrap.dedent(
            f"""\
            [package]
            name = "luaskills-luajit-builder"
            version = "0.1.0"
            edition = "2024"
            publish = false

            [dependencies]
            {mlua_dependency_line}
            """
        ),
        encoding="utf-8",
    )
    (source_dir / "main.rs").write_text(
        textwrap.dedent(
            """\
            //! Minimal crate that asks mlua-sys to build vendored LuaJIT artifacts.
            //! 请求 mlua-sys 构建 vendored LuaJIT 产物的最小 crate。

            /// Keep one tiny binary target so Cargo resolves and builds the vendored LuaJIT dependency graph.
            /// 保留一个极小二进制目标，使 Cargo 解析并构建 vendored LuaJIT 依赖图。
            fn main() {}
            """
        ),
        encoding="utf-8",
    )
    return builder_root / "Cargo.toml"


def run_cargo_build(builder_manifest: Path, profile: str, target_dir: Path) -> Path:
    """Run Cargo for the tiny LuaJIT builder crate into the luaskills target directory.
    将极小 LuaJIT builder crate 的 Cargo 构建输出写入 luaskills 的 target 目录。
    """

    command = ["cargo", "build", "--manifest-path", str(builder_manifest), "--target-dir", str(target_dir)]
    if profile == "release":
        command.append("--release")
    subprocess.run(command, cwd=builder_manifest.parent, check=True)
    return target_dir


def find_newest_file(root: Path, names: set[str]) -> Path | None:
    """Find the newest file whose name matches one of the requested names.
    查找文件名命中请求集合的最新文件。
    """

    matches = [path for path in root.rglob("*") if path.is_file() and path.name in names]
    if not matches:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime)


def find_files_by_patterns(root: Path, patterns: list[str]) -> list[Path]:
    """Find files whose names match one of the requested glob patterns.
    查找文件名命中任一请求 glob 模式的文件。
    """

    matches: dict[str, Path] = {}
    for pattern in patterns:
        for path in root.rglob(pattern):
            if path.is_file():
                matches[str(path.resolve())] = path
    return sorted(matches.values(), key=lambda path: (path.name, str(path)))


def has_runtime_library(root: Path, platform: str) -> bool:
    """Return whether the tree already contains a runtime Lua ABI provider.
    返回目录树中是否已经包含运行时 Lua ABI 提供库。
    """

    runtime_patterns = RUNTIME_LIBRARY_PATTERNS.get(platform)
    if not runtime_patterns:
        raise ValueError(f"unsupported platform for LuaJIT SDK build: {platform}")
    return bool(find_files_by_patterns(root, runtime_patterns))


def find_newest_header_dir(root: Path) -> Path | None:
    """Find the newest directory that contains LuaJIT C API headers.
    查找包含 LuaJIT C API 头文件的最新目录。
    """

    candidates = []
    for header in root.rglob("lua.h"):
        directory = header.parent
        if (directory / "lauxlib.h").exists() and (directory / "luajit.h").exists():
            candidates.append(directory)
    if not candidates:
        return None
    return max(candidates, key=lambda path: max(child.stat().st_mtime for child in path.glob("*.h")))


def find_newest_luajit_source_dir(root: Path) -> Path | None:
    """Find the newest LuaJIT source directory generated by mlua-sys.
    查找 mlua-sys 生成的最新 LuaJIT 源码目录。
    """

    candidates = []
    for build_script in root.rglob("msvcbuild.bat"):
        directory = build_script.parent
        if (directory / "lua.h").exists() and (directory / "luajit.h").exists():
            candidates.append(directory)
    for makefile in root.rglob("Makefile"):
        directory = makefile.parent
        if (directory / "lua.h").exists() and (directory / "luajit.h").exists():
            candidates.append(directory)
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def copy_headers(header_dir: Path, output_dir: Path) -> None:
    """Copy LuaJIT C API headers into the output include directory.
    将 LuaJIT C API 头文件复制到输出 include 目录。
    """

    include_dir = output_dir / "include"
    include_dir.mkdir(parents=True, exist_ok=True)
    for header in header_dir.glob("*.h"):
        shutil.copy2(header, include_dir / header.name)


def ensure_windows_lua51_dll(target_dir: Path) -> None:
    """Build lua51.dll from the mlua-sys LuaJIT source tree when Cargo only produced import libs.
    当 Cargo 仅产出导入库时，从 mlua-sys 的 LuaJIT 源码树构建 lua51.dll。
    """

    if find_newest_file(target_dir, {"lua51.dll"}) is not None:
        return

    source_dir = find_newest_luajit_source_dir(target_dir)
    if source_dir is None:
        raise FileNotFoundError(f"LuaJIT source directory was not found under {target_dir}")
    build_script = source_dir / "msvcbuild.bat"
    if not build_script.exists():
        raise FileNotFoundError(f"LuaJIT msvcbuild.bat was not found under {source_dir}")

    run_windows_msvc_build(build_script)
    if not (source_dir / "lua51.dll").exists():
        raise FileNotFoundError(f"LuaJIT msvcbuild.bat did not produce lua51.dll under {source_dir}")


def find_vswhere() -> Path | None:
    """Find the Visual Studio installer discovery tool when it is available.
    在可用时查找 Visual Studio 安装发现工具。
    """

    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def find_vcvarsall() -> Path | None:
    """Find vcvarsall.bat for a local Visual Studio C++ toolchain.
    查找本地 Visual Studio C++ 工具链的 vcvarsall.bat。
    """

    vswhere = find_vswhere()
    if vswhere is not None:
        result = subprocess.run(
            [
                str(vswhere),
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        install_path = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        if install_path:
            candidate = Path(install_path) / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
            if candidate.exists():
                return candidate
    return None


def run_windows_msvc_build(build_script: Path) -> None:
    """Run LuaJIT's MSVC build script through a temporary batch wrapper.
    通过临时批处理包装器运行 LuaJIT 的 MSVC 构建脚本。
    """

    vcvarsall = None if shutil.which("cl.exe") and shutil.which("nmake.exe") else find_vcvarsall()
    if vcvarsall is None and not (shutil.which("cl.exe") and shutil.which("nmake.exe")):
        raise FileNotFoundError(
            "Visual Studio C++ build environment was not active and vcvarsall.bat was not found"
        )

    wrapper_path = build_script.parent / "_luaskills_build_lua51.bat"
    lines = ["@echo off", "setlocal"]
    if vcvarsall is not None:
        lines.extend(
            [
                f'call "{vcvarsall}" amd64',
                "if errorlevel 1 exit /b %errorlevel%",
            ]
        )
    lines.extend(
        [
            f'call "{build_script}"',
            "exit /b %errorlevel%",
        ]
    )
    wrapper_path.write_text("\r\n".join(lines) + "\r\n", encoding="ascii")
    try:
        subprocess.run(["cmd.exe", "/d", "/c", str(wrapper_path)], cwd=build_script.parent, check=True)
    finally:
        wrapper_path.unlink(missing_ok=True)


def unix_luajit_make_env(platform: str) -> dict[str, str]:
    """Build the make environment used for a dynamic LuaJIT rebuild on Unix platforms.
    构造 Unix 平台动态重建 LuaJIT 使用的 make 环境。
    """

    environment = os.environ.copy()
    if platform.startswith("linux-"):
        environment.setdefault("TARGET_SYS", "Linux")
    elif platform == "macos-x64":
        environment.setdefault("TARGET_SYS", "Darwin")
        environment.setdefault("MACOSX_DEPLOYMENT_TARGET", "10.14")
    elif platform == "macos-arm64":
        environment.setdefault("TARGET_SYS", "Darwin")
        environment.setdefault("MACOSX_DEPLOYMENT_TARGET", "11.0")
    else:
        raise ValueError(f"unsupported Unix platform for LuaJIT dynamic rebuild: {platform}")
    return environment


def run_unix_luajit_dynamic_build(source_dir: Path, platform: str) -> None:
    """Run LuaJIT's makefile in dynamic mode for Unix runtime libraries.
    以 dynamic 模式运行 LuaJIT makefile 以生成 Unix 运行时库。
    """

    make = shutil.which("make")
    if make is None:
        raise FileNotFoundError("make was not found; it is required to build LuaJIT dynamic libraries")

    environment = unix_luajit_make_env(platform)
    subprocess.run([make, "clean"], cwd=source_dir, env=environment, check=False)
    jobs = str(os.cpu_count() or 2)
    subprocess.run(
        [make, f"-j{jobs}", "BUILDMODE=dynamic"],
        cwd=source_dir,
        env=environment,
        check=True,
    )


def read_elf_soname(library_path: Path) -> str:
    """Read the ELF SONAME from a Linux shared library when readelf is available.
    在 readelf 可用时读取 Linux 共享库的 ELF SONAME。
    """

    readelf = shutil.which("readelf")
    if readelf is None:
        return ""
    result = subprocess.run(
        [readelf, "-d", str(library_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    match = re.search(r"Library soname:\s*\[([^\]]+)\]", result.stdout)
    return match.group(1) if match else ""


def ensure_linux_soname_aliases(output_dir: Path) -> list[str]:
    """Create Linux LuaJIT compatibility aliases from the produced shared library SONAME.
    根据产出的共享库 SONAME 创建 Linux LuaJIT 兼容别名。
    """

    source = next(iter(output_dir.glob("libluajit.so*")), None)
    if source is None:
        return []

    alias_names = ["libluajit-5.1.so"]
    soname = read_elf_soname(source)
    if soname:
        alias_names.append(soname)

    created: list[str] = []
    for alias_name in alias_names:
        destination = output_dir / alias_name
        if destination.exists():
            continue
        shutil.copy2(source, destination)
        created.append(alias_name)
    return created


def ensure_macos_dylib_aliases(output_dir: Path) -> list[str]:
    """Create macOS dylib compatibility aliases when LuaJIT emits a so-named Mach-O library.
    当 LuaJIT 产出 so 命名的 Mach-O 库时创建 macOS dylib 兼容别名。
    """

    source = next(iter(output_dir.glob("libluajit.so*")), None)
    if source is None:
        return []

    alias_names = ["libluajit.dylib", "libluajit-5.1.dylib"]
    created: list[str] = []
    for alias_name in alias_names:
        destination = output_dir / alias_name
        if destination.exists():
            continue
        shutil.copy2(source, destination)
        created.append(alias_name)
    return created


def copy_file_alias(source: Path, destination: Path) -> bool:
    """Copy one file alias when it does not already exist.
    在目标文件尚不存在时复制一个文件别名。
    """

    if destination.exists():
        return False
    shutil.copy2(source, destination)
    return True


def ensure_luajit_interpreter_aliases(output_dir: Path, platform: str) -> list[str]:
    """Create Lua interpreter aliases expected by LuaRocks configure probes.
    创建 LuaRocks configure 探测所期望的 Lua 解释器别名。
    """

    if platform == "windows-x64":
        interpreter = output_dir / "luajit.exe"
        alias_names = ["lua.exe", "lua5.1.exe"]
    else:
        interpreter = output_dir / "luajit"
        alias_names = ["lua", "lua5.1"]

    if not interpreter.exists():
        return []

    bin_dir = output_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for alias_name in alias_names:
        root_alias = output_dir / alias_name
        bin_alias = bin_dir / alias_name
        if copy_file_alias(interpreter, root_alias):
            created.append(alias_name)
        if copy_file_alias(interpreter, bin_alias):
            created.append(f"bin/{alias_name}")
    return created


def copy_unix_luajit_runtime_libraries(source_dir: Path, output_dir: Path) -> list[str]:
    """Copy dynamic LuaJIT runtime libraries from one build source directory.
    从单个构建源码目录复制动态 LuaJIT 运行时库。
    """

    copied: list[str] = []
    seen_names: set[str] = set()
    patterns = ["libluajit-5.1.so*", "libluajit.so*", "libluajit-5.1*.dylib*", "libluajit.dylib*"]
    for source in find_files_by_patterns(source_dir, patterns):
        if source.name in seen_names:
            continue
        destination = output_dir / source.name
        shutil.copy2(source, destination)
        copied.append(source.name)
        seen_names.add(source.name)
    return copied


def ensure_unix_luajit_runtime_library(target_dir: Path, output_dir: Path, platform: str) -> list[str]:
    """Build a dynamic LuaJIT runtime library in an isolated source copy when Cargo only produced static artifacts.
    当 Cargo 仅产出静态产物时，在隔离的源码副本中构建动态 LuaJIT 运行时库。
    """

    if has_runtime_library(output_dir, platform):
        return []

    source_dir = find_newest_luajit_source_dir(target_dir)
    if source_dir is None:
        raise FileNotFoundError(f"LuaJIT source directory was not found under {target_dir}")

    with tempfile.TemporaryDirectory(prefix="luaskills-luajit-dynamic-") as temp_root:
        scratch_build_root = Path(temp_root) / "luajit-build"
        shutil.copytree(
            source_dir.parent,
            scratch_build_root,
            ignore=shutil.ignore_patterns("*.o", "*.a", "*.so*", "*.dylib*", "luajit"),
        )
        scratch_source = scratch_build_root / "src"
        run_unix_luajit_dynamic_build(scratch_source, platform)
        copied = copy_unix_luajit_runtime_libraries(scratch_source, output_dir)

    if not has_runtime_library(output_dir, platform):
        raise FileNotFoundError(f"LuaJIT dynamic rebuild did not produce a runtime ABI provider for {platform}")
    return copied


def copy_builder_artifacts(target_dir: Path, output_dir: Path, platform: str) -> list[str]:
    """Copy LuaJIT build artifacts from the Cargo target tree into the SDK directory.
    将 Cargo target 树中的 LuaJIT 构建产物复制到 SDK 目录。
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    if platform == "windows-x64":
        ensure_windows_lua51_dll(target_dir)

    copied: list[str] = []
    seen_names: set[str] = set()
    for source in find_files_by_patterns(target_dir, ARTIFACT_PATTERNS):
        if source.name in seen_names:
            continue
        destination = output_dir / source.name
        shutil.copy2(source, destination)
        copied.append(source.name)
        seen_names.add(source.name)

    if platform != "windows-x64":
        copied.extend(ensure_unix_luajit_runtime_library(target_dir, output_dir, platform))

    if not has_runtime_library(output_dir, platform):
        raise FileNotFoundError(
            f"LuaJIT runtime ABI provider was not produced for {platform}; copied={copied}"
        )
    if platform.startswith("linux-"):
        copied.extend(ensure_linux_soname_aliases(output_dir))
    if platform.startswith("macos-"):
        copied.extend(ensure_macos_dylib_aliases(output_dir))
    copied.extend(ensure_luajit_interpreter_aliases(output_dir, platform))
    return copied


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the LuaJIT SDK builder.
    解析 LuaJIT SDK 构建器的命令行参数。
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--profile", choices=["debug", "release"], default="release")
    parser.add_argument("--luaskills-root", default="")
    return parser.parse_args()


def main() -> int:
    """Run the minimal Rust-backed LuaJIT SDK build workflow.
    执行基于最小 Rust 项目的 LuaJIT SDK 构建流程。
    """

    args = parse_args()
    root = repo_root()
    luaskills_root = resolve_luaskills_root(root, args.luaskills_root)
    mlua_dependency_line = read_mlua_dependency_line(luaskills_root)
    builder_manifest = write_builder_crate(root / "target" / "luajit-builder", mlua_dependency_line)
    output_dir = Path(args.output_dir).resolve()

    print(f"Using mlua dependency from {luaskills_root / 'Cargo.toml'}")
    print(f"mlua dependency: {mlua_dependency_line}")
    target_dir = run_cargo_build(builder_manifest, args.profile, luaskills_root / "target")
    header_dir = find_newest_header_dir(target_dir)
    if header_dir is None:
        raise FileNotFoundError(f"LuaJIT headers were not found under {target_dir}")

    copy_headers(header_dir, output_dir)
    copied = copy_builder_artifacts(target_dir, output_dir, args.platform)
    print(f"LuaJIT SDK ready at {output_dir}")
    print(f"Copied artifacts: {', '.join(copied)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
