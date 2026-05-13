[app]
title = Personal VPN
package.name = personalvpn
package.domain = com.ehsanpoursamad.personalvpn
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0.0
requirements = python3,kivy==2.3.0,cryptography,h2,brotli,zstandard
orientation = portrait
fullscreen = 1
android.api = 33
android.minapi = 21
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_SETTINGS,ACCESS_WIFI_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.arch = arm64-v8a
android.presplash_color = #FFFFFF
android.accept_sdk_license = True
android.gradle_dependencies = 
p4a.branch = master
android.services = proxy_service:foreground
