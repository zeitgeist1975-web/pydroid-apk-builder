[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas  # 리소스 파일 포함 권장
# 앱에서 인터넷을 쓴다면 requests, certifi 추가 필수
requirements = python3,kivy,requests,certifi 
orientation = portrait
fullscreen = 1
version = 1.0

# [Android 핵심 설정 - 이대로 고정하세요]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
android.archs = arm64-v8a  # 테스트용은 하나만 설정하여 빌드 속도 2배 향상

# [빌드 최적화]
android.skip_update = False
android.copy_libs = 1

[buildozer]
log_level = 2
warn_on_root = 1
