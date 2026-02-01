[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt

# 핵심 수정: 버전 정보가 반드시 있어야 합니다.
version = 1.0.0

# 아래 설정들도 정확한지 확인하세요.
requirements = python3,kivy==2.2.1,requests,certifi,urllib3,openssl
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
