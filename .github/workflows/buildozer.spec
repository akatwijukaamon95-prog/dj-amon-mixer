[app]
title = DJ Amon Mixer
package.name = djamonmixer
package.domain = org.amon
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0
requirements = python3,kivy==2.3.0,pyjnius,android
orientation = portrait
fullscreen = 0
android.permissions = RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_AUDIO
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
