[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt

version = 1.0.0

requirements = python3,kivy==2.2.1,requests,certifi,urllib3,openssl,pypdf2,deep-translator
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
