-- Windows override / Windows 覆盖版
-- Notes / 说明:
-- Switch lyaml to LuaRocks' builtin builder on Windows because the upstream luke-based build assumes Unix shell semantics.
-- 由于 upstream 的 luke 构建流程依赖 Unix shell 语义，这里在 Windows 下改用 LuaRocks builtin builder。

package = "lyaml"
version = "{{version}}"

description = {
  summary = "libYAML binding for Lua",
  detailed = "Read and write YAML format files with Lua.",
  homepage = "https://github.com/gvvaughan/lyaml",
  license = "MIT/X11",
}

source = {
  url = "{{source_url}}",
  dir = "{{source_dir}}",
}

dependencies = {
  "lua >= 5.1, < 5.5",
}

external_dependencies = {
  YAML = {
    library = "yaml",
  },
}

build = {
  type = "builtin",
  modules = {
    yaml = {
      sources = {
        "ext/yaml/yaml.c",
        "ext/yaml/emitter.c",
        "ext/yaml/parser.c",
        "ext/yaml/scanner.c",
      },
      defines = {
        "VERSION=\"{{semantic_version}}\"",
        "YAML_DECLARE_STATIC",
      },
      incdirs = {
        "ext/include",
        "$(LUA_INCDIR)",
        "$(YAML_INCDIR)",
      },
      libdirs = {
        "$(YAML_LIBDIR)",
      },
      libraries = {
        "yaml",
      },
    },
    ["lyaml"] = "lib/lyaml/init.lua",
    ["lyaml.explicit"] = "lib/lyaml/explicit.lua",
    ["lyaml.functional"] = "lib/lyaml/functional.lua",
    ["lyaml.implicit"] = "lib/lyaml/implicit.lua",
  },
}
