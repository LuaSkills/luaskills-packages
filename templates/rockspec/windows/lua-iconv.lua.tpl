-- Windows override / Windows 覆盖版
-- Notes / 说明:
-- Link lua-iconv against the bundled win-iconv static library on Windows.
-- 在 Windows 下将 lua-iconv 静态链接到随 bundle 提供的 win-iconv 静态库。

package = "lua-iconv"
version = "{{version}}"

source = {
  url = "{{source_url}}",
  tag = "{{source_tag}}",
}

description = {
  summary = "Lua binding to the iconv",
  detailed = [[
    Lua binding to the POSIX 'iconv' library, which converts a sequence of
    characters from one codeset into a sequence of corresponding characters
    in another codeset.
  ]],
  homepage = "https://github.com/lunarmodules/lua-iconv",
  license = "MIT/X11",
}

dependencies = {
  "lua >= 5.1",
}

external_dependencies = {
  ICONV = {
    header = "iconv.h",
    library = "libiconv",
  },
}

build = {
  type = "builtin",
  modules = {
    iconv = {
      sources = { "luaiconv.c" },
      incdirs = { "$(ICONV_INCDIR)" },
      libdirs = { "$(ICONV_LIBDIR)" },
      libraries = { "libiconv" },
    },
  },
}
