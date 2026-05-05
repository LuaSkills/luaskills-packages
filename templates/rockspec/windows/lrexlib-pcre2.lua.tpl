-- Windows override / Windows 覆盖版
-- Notes / 说明:
-- Use the static PCRE2 library name shipped by the LuaSkills bundle on Windows.
-- 使用 LuaSkills 在 Windows 下打包的静态 PCRE2 库名。

source = {
  url = "{{source_url}}",
  tag = "{{source_tag}}",
}

description = {
  summary = "Regular expression library binding (PCRE2 flavour).",
  detailed = "Lrexlib is a regular expression library for Lua 5.1-5.4, which\\\n+provides bindings for several regular expression libraries.\\\n+This rock provides the PCRE2 bindings.",
  license = "MIT/X11",
  homepage = "https://github.com/rrthomas/lrexlib",
}

dependencies = {
  "lua >= 5.1",
}

package = "Lrexlib-PCRE2"
version = "{{version}}"

build = {
  type = "builtin",
  modules = {
    rex_pcre2 = {
      sources = {
        "src/common.c",
        "src/pcre2/lpcre2.c",
        "src/pcre2/lpcre2_f.c",
      },
      defines = {
        "VERSION=\"{{semantic_version}}\"",
        "PCRE2_CODE_UNIT_WIDTH=8",
        "PCRE2_STATIC",
      },
      incdirs = {
        "$(PCRE2_INCDIR)",
      },
      libdirs = {
        "$(PCRE2_LIBDIR)",
      },
      libraries = {
        "pcre2-8-static",
      },
    },
  },
}

external_dependencies = {
  PCRE2 = {
    header = "pcre2.h",
    library = "pcre2-8-static",
  },
}
