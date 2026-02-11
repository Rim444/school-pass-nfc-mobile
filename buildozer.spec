[app]
title = School Pass
package.name = schoolpass
package.domain = org.schoolpass

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,ttf,otf
source.exclude_dirs = tests, bin, .buildozer, .github, __pycache__, *.pyc

version = 1.0.0
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,plyer,pillow,android,pyjnius

orientation = portrait
fullscreen = 0

# Android SDK/NDK — Buildozer сам скачает, не указываем конкретные версии
android.accept_sdk_license = true

# Архитектуры — заменяем android.arch на android.archs
android.archs = arm64-v8a, armeabi-v7a

# Минимальная и целевая версии Android
android.minapi = 21
android.api = 33

# Разрешения
android.permissions = INTERNET, NFC, ACCESS_NETWORK_STATE, WAKE_LOCK, VIBRATE
android.features = android.hardware.nfc, android.hardware.nfc.hce

# Для совместимости
android.gradle_dependencies = 'androidx.appcompat:appcompat:1.6.1', 'com.google.android.material:material:1.9.0'
android.enable_androidx = true

[buildozer]
log_level = 2
warn_on_root = 1