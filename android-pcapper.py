#!/usr/bin/env python
import subprocess
from subprocess import run, Popen
import argparse, argcomplete
import os
from time import sleep
from androguard.core.bytecodes import apk
from androguard.core.bytecodes.axml import AXMLPrinter


app_path = ""
app_name = ""

# TODO: fix argcomplete

def avd_completer(**kwargs):
    try:
        p = run(["emulator", "-list-avds"], capture_output=True)
        return p.stdout.decode("ascii").splitlines()
    except subprocess.CalledProcessError as error:
        print("Could not get avds for tab completion")
        print(error.output)
        exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python android-pcapper.py")
    parser.add_argument("app", help=".apk file or package name")
    parser.add_argument("-avd", help="Android Virtual Device Name to launch", nargs='?', default="Pixel_3_API_28").completer = avd_completer
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.avd is None:
        print(parser.print_usage())
        exit()

    # Download App or use apk
    if not os.path.exists(args.app):
        try:
            print("Downloading .apk ...")
            run(["gplaycli", "-d", args.app])
        except subprocess.CalledProcessError as error:
            print("Could not download " + args.app)
            print(error.output)
            exit()
        # Downloaded
        app_path = args.app + '.apk'
        app_name = args.app
    else:
        # .apk on Filesystem
        app_path = args.app
        app_name = apk.APK(app_path).package  # os.path.splitext(args.app)[0]

    # Check if App is patched already
    user_cert_trusted = False
    apk_file = apk.APK(app_path)
    manifest = apk_file.get_android_manifest_xml()
    if 'res/xml/network_security_config.xml' in apk_file.files.keys():
        print("Network Security Config present in .apk")
        axml = AXMLPrinter(apk_file.get_file('res/xml/network_security_config.xml'))
        axml_obj = axml.get_xml_obj()
        for element in axml_obj.iter("certificates"):
            if element.values() == ['user']:
                print("User certificates trusted by network security configuration")
                user_cert_trusted = True
                break
    if not user_cert_trusted:
        print("User certificates not trusted by network security configuration.")
        print("Patching APK...")
        try:
            p = run(["apk-mitm", app_path], capture_output=False)
            app_path = os.path.splitext(args.app)[0] + "-patched.apk"
        except subprocess.CalledProcessError as error:
            print("Could not patch app with apk-mitm")
            print(error.output)
            exit()

    # Start Android emulator
    print("Starting Android Emulator")
    print("emulator -avd " + args.avd)
    Popen(["emulator", "-avd", args.avd], bufsize=1, universal_newlines=True)

    # Wait for boot
    while True:
        try:
            p = run(["adb", "shell", "getprop", "sys.boot_completed"], capture_output=True)
        except subprocess.CalledProcessError as error:
            print("Could not get boot status from adb")
            print(error.output)
            exit()
        if p.stdout == b'1\n':
            print("AVD booted")
            break;
        else:
            print("not booted yet")
            sleep(1)

    # Check if App is already installed
    try:
        p = run(["adb", "shell", "pm", "list", "packages", app_name], capture_output=True)
    except subprocess.CalledProcessError as error:
        print("Could not get package names from adb")
        print(error.output)
        exit()
    if p.stdout == b'':
        print("App not installed")
        # Install App
        try:
            print("Installing App...")
            p = run(["adb", "install", app_path])
        except subprocess.CalledProcessError as error:
            print("Could not install App")
            print(error.output)
            exit()
    else:
        print("App already installed.")

    # Launch PCAPDroid
    try:
        print("Launching PCAPDroid...")
        run(["adb", "shell", "am", "start", "-e", "action", "start", "-e", "pcap_dump_mode", "http_server", "-e",
             "http_server_port", "8080", "-e", "app_filter", app_name, "-n",
             "com.emanuelef.remote_capture.debug/com.emanuelef.remote_capture.activities.CaptureCtrl"])
    except subprocess.CalledProcessError as error:
        print("Could not launch emulator")
        print(error.output)
        exit()

    # Enable Port Forwarding
    try:
        p = run(["adb", "forward", "tcp:8080", "tcp:8080"], capture_output=True)
    except subprocess.CalledProcessError as error:
        print("Could not enable Port Forwarding")
        print(error.output)
        exit()

    # Start Wireshark
    # sleep(10)
    # try:
    #     print("Starting Wireshark")
    #     # curl -NLs http://192.168.1.10:8080 | wireshark -k -i -
    #     # curl -NLs http://127.0.0.1:8080 | wireshark -k -i -
    #     p1 = run(["curl", "-NLs", "http://127.0.0.1:5123"])
    #     p2 = run(["wireshark", "-k", "-i", "-"])
    # except subprocess.CalledProcessError as error:
    #     print("Could not launch Wireshark")
    #     print(error.output)
    #     exit()

    # sleep(5)
    # # Start App
    # try:
    #     print("Starting App")
    #     p = run(["adb", "shell", "monkey", "-p", app_name, "-c", "android.intent.category.LAUNCHER", "1"],
    #             capture_output=True)
    # except subprocess.CalledProcessError as error:
    #     print("Could not launch App")
    #     print(error.output)
    #     exit()
