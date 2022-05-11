# Android PCAPer
This is a script to automate the process of downloading Apps from Google Play, patching them, installing them on an Android Virtual Device and start a PCAP for that App.

# Requirements
- [Androguard](https://github.com/androguard/androguard)
- [Android emulator](https://developer.android.com/studio/run/emulator-commandline)
- [apk-mitm](https://github.com/shroudedcode/apk-mitm/)
- [gplaycli](https://github.com/besendorf/gplaycli)

# Usage
python android-pcapper.py com.example.app -avd AVD_NAME
