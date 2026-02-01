[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
# requirements: certifi, urllib3 등이 필요한 경우 명시, cython은 설치 단계에서 처리함
requirements = python3,kivy==2.2.1,requests,certifi,urllib3

orientation = portrait
fullscreen = 1
version = 1.0

# Android SDK/NDK 설정 (API 33 대응 최적값)
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.archs = arm64-v8a
android.permissions = INTERNET

# 빌드 속도 및 용량 최적화
android.skip_update = False
android.copy_libs = 1

[buildozer]
log_level = 2
warn_on_root = 1
