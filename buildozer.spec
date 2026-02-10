[app]
title = School Pass
package.name = schoolpass
package.domain = org.schoolpass

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
source.exclude_exts = spec
source.exclude_dirs = bin, .buildozer, __pycache__
source.include_dirs = src

version = 1.0
requirements = python3, kivy==2.3.1, kivymd==1.2.0, requests, pillow, plyer

android.permissions = NFC, INTERNET, ACCESS_NETWORK_STATE, VIBRATE
android.api = 26
android.minapi = 21
android.ndk = 25b
android.sdk = 24
android.arch = arm64-v8a, armeabi-v7a

orientation = portrait
fullscreen = 0
