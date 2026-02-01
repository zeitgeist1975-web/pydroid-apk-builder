[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
# 확장자 사이에 공백이 없어야 합니다.
source.include_exts = py,png,jpg,kv,atlas
# 인터넷 권한이 필요한 경우 아래 permissions 주석을 해제하세요.
android.permissions = INTERNET
requirements = python3,kivy,requests,certifi 
orientation = portrait
fullscreen = 1
version = 1.0

# [Android 핵심 설정 - 주석을 모두 제거했습니다]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
# 아키텍처 설정 뒤에 절대 주석을 달지 마세요.
android.archs = arm64-v8a

# [빌드 최적화]
android.skip_update = False
android.copy_libs = 1

[buildozer]
log_level = 2
warn_on_root = 1
