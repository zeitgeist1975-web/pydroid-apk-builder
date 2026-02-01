[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
requirements = python3,kivy==2.2.1,requests,certifi,urllib3
orientation = portrait
fullscreen = 1
version = 1.0

# Android 핵심 설정
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.archs = arm64-v8a
android.permissions = INTERNET

# 빌드 최적화
android.skip_update = False
android.copy_libs = 1

[buildozer]
log_level = 2
warn_on_root = 1
