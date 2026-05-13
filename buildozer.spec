[app]

# (str) Title of your application
title = Personal VPN

# (str) Package name
package.name = personalvpn

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code directory
source.dir = .

# (list) Source files to include (let buildozer find everything)
source.include_exts = py,png,jpg,kv,atlas,txt,json

# (list) Version control system ignored files
version.git_ignore = True

# (str) Application versioning
version = 0.1

# (list) Application requirements
# REMOVED asyncio (standard library) – it must NOT be listed
requirements = python3,kivy==2.3.0,cryptography,h2,brotli,zstandard

# (str) Supported orientation (portrait, landscape, all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Android API level to use
android.api = 33

# (int) Minimum API level (Android 5.0)
android.minapi = 21

# (int) Android NDK version to use
android.ndk = 25c
android.ndk_version = 25c

# (int) Android NDK API to use (defaults to android.minapi)
android.ndk_api = 21

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (list) Android permissions
android.permissions = INTERNET

# (bool) Enable LDTR (log data to remote) – debugging
android.allow_backup = True

# (str) Android logcat filters (use for debugging)
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a symlink
android.copy_libs = True

# (str) Android arch to build for (use list for multiple)
android.archs = arm64-v8a

# (bool) Turn on verbose build output
log_level = 2

# (bool) Warn if buildozer is run as root
warn_on_root = 1

# ----------------------- iOS only -------------------------
ios.kivy_version = 2.3.0
osx.python_version = 3
