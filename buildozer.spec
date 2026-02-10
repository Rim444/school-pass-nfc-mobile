[app]
title = School Pass
package.name = schoolpass
package.domain = org.schoolpass

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,ttf,otf
source.exclude_dirs = tests, bin, .buildozer, .github, __pycache__, *.pyc

version = 1.0.0
requirements = 
    python3,
    kivy==2.3.1,
    kivymd==1.2.0,
    requests==2.31.0,
    plyer==2.1.0,
    pillow==10.1.0,
    android,
    pyjnius

orientation = portrait
fullscreen = 0

# Android конфигурация
android.api = 34
android.minapi = 21
android.ndk = 23b
android.sdk = 34
android.ndk_api = 21
android.arch = arm64-v8a,armeabi-v7a
android.p4a_dir = /home/runner/.local/lib/python3.9/site-packages/pythonforandroid

# Разрешения для NFC
android.permissions = 
    INTERNET,
    NFC,
    ACCESS_NETWORK_STATE,
    WAKE_LOCK,
    VIBRATE

# NFC features
android.features = 
    android.hardware.nfc,
    android.hardware.nfc.hce

# Gradle зависимости для NFC
android.gradle_dependencies = 
    'androidx.appcompat:appcompat:1.6.1',
    'com.google.android.material:material:1.9.0'

# Икони (добавьте свои файлы в data/)
# icon.filename = data/icon.png
# presplash.filename = data/presplash.png
presplash.color = #2196F3

# Оптимизация сборки
android.allow_backup = true
android.accept_sdk_license = true
android.enable_androidx = true

[buildozer]
log_level = 2
warn_on_root = 1
