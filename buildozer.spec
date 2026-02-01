[app]
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt

# 아래 버전 정보가 누락되었거나 주석(#) 처리되어 있는지 확인하세요.
version = 1.0.0

# (권장) 라이브러리 및 API 설정
requirements = python3,kivy==2.2.1,requests,certifi,urllib3,openssl
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
