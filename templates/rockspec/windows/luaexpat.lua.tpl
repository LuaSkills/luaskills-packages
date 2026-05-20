-- Windows override / Windows 覆盖版
-- Notes / 说明:
-- Use the bundled libexpat import library name on Windows instead of the upstream Unix-oriented default.
-- 在 Windows 下使用随 bundle 提供的 libexpat 导入库名，而不是上游面向 Unix 的默认配置。

package = "luaexpat"
version = "{{version}}"

source = {
  url = "{{source_url}}",
  tag = "{{source_tag}}",
}

description = {
  summary = "XML Expat parsing",
  detailed = [[
    LuaExpat is a SAX (Simple API for XML) XML parser based on the
    Expat library.
  ]],
  homepage = "https://lunarmodules.github.io/luaexpat",
  license = "MIT/X11",
}

dependencies = {
  "lua >= 5.1",
}

external_dependencies = {
  EXPAT = {
    header = "expat.h",
    library = "libexpat",
  },
}

build = {
  type = "builtin",
  modules = {
    lxp = {
      sources = { "src/lxplib.c" },
      libraries = { "libexpat" },
      incdirs = { "$(EXPAT_INCDIR)", "src/" },
      libdirs = { "$(EXPAT_LIBDIR)" },
    },
    ["lxp.lom"] = "src/lxp/lom.lua",
    ["lxp.totable"] = "src/lxp/totable.lua",
    ["lxp.threat"] = "src/lxp/threat.lua",
  },
  copy_directories = { "docs" },
}
