[app]

# (str) Title of your application
title = Taiwan Basketball GM

# (str) Package name
package.name = tbgm

# (str) Package domain (needed for android/ios packaging)
package.domain = org.antigravity

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,enc

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*/*.jpg

# (list) List of directory to exclude (let empty to not exclude everything)
source.exclude_dirs = tests, bin, venv, .git, .gemini, game_saves

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg,*.json

# (str) Application versioning (method 1)
version = 0.7.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3==3.11.9,flet,android,jnius,cryptography,google-auth,google-auth-oauthlib,google-api-python-client,numpy,pandas,openpyxl,httpx,idna,httpcore,sniffio
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
# Valid options are: landscape, portrait, portrait-reverse or landscape-reverse
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for new android toolchain)
# Supported formats are: #RRGGBB #AARRGGBB or one of the following names:
# red, blue, green, black, white, gray, cyan, magenta, yellow, lightgray,
# darkgray, grey, lightgrey, darkgrey, aqua, fuchsia, lime, maroon, navy,
# olive, purple, silver, teal.
android.presplash_color = #003460

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 20

# (str) Android NDK version to use
#android.ndk = 19b

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (str) Android additional libraries to copy into libs/armeabi
#android.add_libs_armeabi = libs/android/*.so
#android.add_libs_armeabi_v7a = libs/android-v7/*.so
#android.add_libs_arm64_v8a = libs/android-v8/*.so
#android.add_libs_x86 = libs/android-x86/*.so
#android.add_libs_mips = libs/android-mips/*.so

# (bool) Indicate whether the screen should stay on
# Don't sleep on Android
android.wakelock = True

# (list) Android application meta-data to set (key=value format)
# Replace VALUE with your actual AdMob App ID (This is the Test ID)
android.meta_data = com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-8287106746857092~6837905197

# (list) Android shared libraries to be added to the application native libs
#android.add_libs =

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (list) Android app theme, default is ok for Kivy-based app
#android.apptheme = "@android:style/Theme.NoTitleBar"

# (list) Pattern to exclude from the final apk
#android.whitelist =

# (bool) Setup the app to not be backupable
#android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk or aar).
#android.release_artifact = aab

# (str) The format used to package the app for debug mode (apk or aar).
#android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android fork to use, defaults to upstream (kivy)
#p4a.fork = kivy

# (str) python-for-android branch to use, defaults to master
#p4a.branch = master

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
#p4a.source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
#p4a.local_recipes =

# (str) Filename to the hook for p4a
#p4a.hook =

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2

# (int) Port number to specify an explicit --port= p4a argument (eg for bootstrap flask)
#p4a.port = 

# Control whether the pyjnius java class generation is enabled
#p4a.pyjnius_class_generation = 0

# (list) Gradle dependencies to add
android.gradle_dependencies = com.google.android.gms:play-services-ads:23.0.0


#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios
# (str) Name of the certificate to use for signing the debug version
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"
# (str) Name of the certificate to use for signing the release version
#ios.codesign.release = %(ios.codesign.debug)s

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output storage, absolute or relative to spec file
# bin_dir = ./bin

#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the "list" as [section:name].
#    Each line will be considered as a option to the list.
#    Let's figure out for "source.include_exts" :
#
#    [app:source.include_exts]
#    py
#    png
#    jpg
#    kv
#    atlas
#
#    -----------------------------------------------------------------------------
#    Profiles
#
#    You can extend section / key with a profile
#    For example, you want to deploy a demo version of your application without
#    HD content. You could first change the title to add "(demo)" in the name
#    and extend the excluded directories to remove the hd content.
#
#    [app@demo]
#    title = My Application (demo)
#
#    [app:source.exclude_patterns@demo]
#    images/hd/*
#
#    Then, invoke buildozer with the "demo" profile :
#
#    buildozer --profile demo android debug
