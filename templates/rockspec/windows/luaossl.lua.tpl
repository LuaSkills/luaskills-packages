-- Windows override / Windows 覆盖版
-- Notes / 说明:
-- Align luaossl with the OpenSSL 3 library names and extra Windows system libraries used by the official LuaSkills runtime bundle.
-- 让 luaossl 与官方 LuaSkills runtime bundle 使用的 OpenSSL 3 库名和额外 Windows 系统库保持一致。

package = "luaossl"
version = "{{version}}"

source = {
  url = "{{source_url}}";
  md5 = "{{source_md5}}";
  dir = "{{source_dir}}";
}

description = {
  summary = "Most comprehensive OpenSSL module in the Lua universe.";
  homepage = "http://25thandclement.com/~william/projects/luaossl.html";
  license = "MIT/X11";
}

supported_platforms = {
  "unix";
  "windows";
}

dependencies = {
  "lua";
}

external_dependencies = {
  OPENSSL = {
    header = "openssl/ssl.h";
    library = "ssl";
  };
  CRYPTO = {
    header = "openssl/crypto.h";
    library = "crypto";
  };
  platforms = {
    windows = {
      OPENSSL = {
        library = "libssl"
      };
      CRYPTO = {
        library = "libcrypto"
      };
    };
  };
}

build = {
  type = "builtin";
  modules = {
    ["_openssl"] = {
      sources = {
        "src/openssl.c";
        "vendor/compat53/c-api/compat-5.3.c";
      };
      libraries = {
        "ssl";
        "crypto";
      };
      defines = {
        "_REENTRANT"; "_THREAD_SAFE";
        "COMPAT53_PREFIX=luaossl";
      };
      incdirs = {
        "$(OPENSSL_INCDIR)";
        "$(CRYPTO_INCDIR)";
      };
      libdirs = {
        "$(OPENSSL_LIBDIR)";
        "$(CRYPTO_LIBDIR)";
      };
    };
    ["openssl"] = "src/openssl.lua";
    ["openssl.auxlib"] = "src/openssl.auxlib.lua";
    ["openssl.bignum"] = "src/openssl.bignum.lua";
    ["openssl.cipher"] = "src/openssl.cipher.lua";
    ["openssl.des"] = "src/openssl.des.lua";
    ["openssl.digest"] = "src/openssl.digest.lua";
    ["openssl.hmac"] = "src/openssl.hmac.lua";
    ["openssl.kdf"] = "src/openssl.kdf.lua";
    ["openssl.ocsp.basic"] = "src/openssl.ocsp.basic.lua";
    ["openssl.ocsp.response"] = "src/openssl.ocsp.response.lua";
    ["openssl.pkcs12"] = "src/openssl.pkcs12.lua";
    ["openssl.pkey"] = "src/openssl.pkey.lua";
    ["openssl.pubkey"] = "src/openssl.pubkey.lua";
    ["openssl.rand"] = "src/openssl.rand.lua";
    ["openssl.ssl.context"] = "src/openssl.ssl.context.lua";
    ["openssl.ssl"] = "src/openssl.ssl.lua";
    ["openssl.x509"] = "src/openssl.x509.lua";
    ["openssl.x509.altname"] = "src/openssl.x509.altname.lua";
    ["openssl.x509.chain"] = "src/openssl.x509.chain.lua";
    ["openssl.x509.crl"] = "src/openssl.x509.crl.lua";
    ["openssl.x509.csr"] = "src/openssl.x509.csr.lua";
    ["openssl.x509.extension"] = "src/openssl.x509.extension.lua";
    ["openssl.x509.name"] = "src/openssl.x509.name.lua";
    ["openssl.x509.store"] = "src/openssl.x509.store.lua";
    ["openssl.x509.verify_param"] = "src/openssl.x509.verify_param.lua";
  };
  platforms = {
    unix = {
      modules = {
        ["_openssl"] = {
          libraries = {
            nil, nil;
            "pthread";
            "m";
          };
          defines = {
            nil, nil, nil;
            "_GNU_SOURCE";
          }
        };
      };
    };
    linux = {
      modules = {
        ["_openssl"] = {
          libraries = {
            nil, nil, nil, nil;
            "dl";
          };
        };
      };
    };
    win32 = {
      modules = {
        ["_openssl"] = {
          libraries = {
            "libssl";
            "libcrypto";
            "ws2_32";
            "advapi32";
            "crypt32";
            "user32";
            "kernel32";
          };
          defines = {
            nil, nil, nil;
            "HAVE_SYS_PARAM_H=0";
            "HAVE_DLFCN_H=0";
            "_WIN32_WINNT=0x0600";
          };
        };
      };
    };
  };
  patches = {
    ["config.h.diff"] = [[
--- a/src/openssl.c
+++ b/src/openssl.c
@@ -26,3 +26 @@
-#if HAVE_CONFIG_H
-#include "config.h"
-#endif
+#include "../config.h.guess"
]];
  }
}
