[app]
title = School Pass
package.name = schoolpass
package.domain = org.schoolpass

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests, bin, .buildozer, .github, __pycache__, *.pyc

version = 1.0.0
requirements = python3,kivy==2.2.1,kivymd==2.0.1

orientation = portrait
fullscreen = 0

# Android SDK/NDK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# Разрешения (только необходимые)
android.permissions = INTERNET, NFC
android.accept_sdk_license = true

# Отключаем предупреждение о root
[buildozer]
log_level = 2
warn_on_root = 0
