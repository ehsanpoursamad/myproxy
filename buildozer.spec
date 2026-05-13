[app]
title = Personal VPN
package.name = personalvpn
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 0.1
requirements = python3,kivy==2.3.0,pyjnius
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
android.accept_sdk_license = True
android.skip_update = True
android.minapi = 21
android.api = 33
android.archs = arm64-v8a
android.permissions = INTERNET,FOREGROUND_SERVICE
android.features =
