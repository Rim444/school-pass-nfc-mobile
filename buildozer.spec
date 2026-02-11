[app]
title = School Pass
package.name = schoolpass
package.domain = org.schoolpass
source.dir = .
version = 1.0
requirements = python3,kivy==2.1.0,kivymd==1.1.1,requests,plyer
orientation = portrait

# Android
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 23b
android.arch = arm64-v8a

# Permissions
android.permissions = INTERNET,NFC

[buildozer]
log_level = 2