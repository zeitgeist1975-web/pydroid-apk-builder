[app]
title = Medical Translator
package.name = medicaltranslator
package.domain = org.medical
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
version = 1.4.0

orientation = portrait

requirements = python3,kivy==2.2.1,PyPDF2==3.0.1,pyjnius

android.api = 28
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
