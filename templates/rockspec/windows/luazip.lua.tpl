-- Windows override / Windows 覆盖版
-- Notes / 说明:
-- Use the actual zziplib import library name generated on Windows instead of the upstream Unix-oriented default.
-- 在 Windows 下使用 zziplib 实际生成的导入库名，而不是上游面向 Unix 的默认链接名。

package = "LuaZip"
version = "{{version}}"

source = {
  url = "{{source_url}}",
  tag = "{{source_tag}}",
}

description = {
  summary = "Library for reading files inside zip files",
  detailed = [[
LuaZip is a lightweight Lua extension library used to read files
stored inside zip files. The API is very similar to the standard
Lua I/O library API.
  ]],
  homepage = "https://github.com/mpeterv/luazip",
  license = "MIT",
}

dependencies = {
  "lua >= 5.1, < 5.4",
}

external_dependencies = {
  ZZIP = {
    header = "zzip/zzip.h",
    library = "zzip-0",
  },
}

build = {
  type = "builtin",
  modules = {
    zip = {
      incdirs = {
        "$(ZZIP_INCDIR)",
      },
      libdirs = {
        "$(ZZIP_LIBDIR)",
      },
      libraries = {
        "zzip-0",
      },
      sources = "src/luazip.c",
    },
  },
}
