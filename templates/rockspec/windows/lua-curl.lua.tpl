-- Windows override / Windows 覆盖版
-- Notes / 说明:
-- Point LuaRocks at the project-provided curl headers and import library on Windows.
-- 在 Windows 下使用项目预编译的 curl 头文件与导入库。

package = "Lua-cURL"
version = "{{version}}"

source = {
  url = "{{source_url}}",
  dir = "{{source_dir}}",
}

description = {
  summary = "Lua binding to libcurl",
  detailed = [[
  ]],
  homepage = "https://github.com/Lua-cURL",
  license  = "MIT/X11"
}

dependencies = {
  "lua >= 5.1, < 5.5"
}

external_dependencies = {
  CURL = {
    header  = "curl/curl.h",
    library = "libcurl_imp",
  }
}

build = {
  copy_directories = {"doc", "examples", "test"},

  type = "builtin",

  modules = {
    ["cURL"           ] = "src/lua/cURL.lua",
    ["cURL.safe"      ] = "src/lua/cURL/safe.lua",
    ["cURL.utils"     ] = "src/lua/cURL/utils.lua",
    ["cURL.impl.cURL" ] = "src/lua/cURL/impl/cURL.lua",

    lcurl = {
      libraries = {"libcurl_imp", "ws2_32"},
      sources = {
        "src/l52util.c",    "src/lceasy.c", "src/lcerror.c",
        "src/lchttppost.c", "src/lcurl.c",  "src/lcutils.c",
        "src/lcmulti.c",    "src/lcshare.c", "src/lcmime.c",
        "src/lcurlapi.c",
      },
      incdirs   = { "$(CURL_INCDIR)" },
      libdirs   = { "$(CURL_LIBDIR)" }
    },
  }
}
