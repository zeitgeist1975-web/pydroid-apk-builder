[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
# 필요한 라이브러리를 명시합니다.
[span_11](start_span)requirements = python3,kivy==2.2.1,requests,certifi,urllib3[span_11](end_span)

orientation = portrait
fullscreen = 1
version = 1.0

# Android 핵심 설정 (API 33 및 NDK 25b 권장)
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.archs = arm64-v8a
[span_12](start_span)android.permissions = INTERNET[span_12](end_span)

# 빌드 최적화
android.skip_update = False
android.copy_libs = 1

[buildozer]
log_level = 2
[span_13](start_span)warn_on_root = 1[span_13](end_span)
