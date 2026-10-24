# Install HorizonX 3.5.1

## APK from a USB drive

1. [Download HorizonX-3.5.1.apk](https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-3.5.1.apk) on your PC or phone. Copy the APK file to a USB drive and remember its folder.
2. Connect the USB drive to your TV. Open a file manager, select your USB drive and find the APK.
3. Select **Install**. If HorizonX is already installed, the button says **Update**. If Android blocks installation, open Settings from that prompt, allow your file manager to install apps, then return to the APK.
4. Confirm **Install** or **Update** in Android's installer. Select **Open** when it finishes.
5. In HorizonX, open the **Settings gear → System → Set up HorizonX**.
6. Select **TV information**. Highlight **Build** and press OK seven times to enable Developer options. If Developer options are already enabled, continue.
7. Go back to **Set up HorizonX → Developer options**. Enable **USB debugging** or **ADB debugging**, depending on your TV. Keep debugging on while using a PC connection.
8. Return to HorizonX and select **Authorize ADB connection**. If **Allow debugging?** appears, select **Always allow** and confirm.
9. Select **Use HorizonX as home → Activate Home**.
10. Press **Home** on your remote, including from another app, to check that HorizonX opens.

[Watch the full USB tutorial](https://raw.githubusercontent.com/2207juan/HorizonX/main/docs/media/install-usb-en.mp4) · [Español](GUIA.md)

The TV information and Developer options buttons open Android's public settings panels. Names vary by TV manufacturer. Installing the APK and selecting Home are separate operations. Local activation requires a firmware that exposes local ADB and the owner's authorization. If activation fails or local ADB is unavailable, use the PC assistant below. Do not uninstall HorizonX to update it; keeping the same installation preserves its data.

## ADB from a PC

1. [Download the PC ZIP](https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-PC-3.5.1.zip) and extract it. It contains the APK.
2. Install Python 3.10+ and [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools). Add Platform Tools to PATH, or place its `platform-tools` folder next to `horizonx.py`.
3. Enable the TV's debugging options. If wireless debugging requires pairing, pair and connect using the separate ports shown by the TV:

```sh
adb pair TV_IP:PAIRING_PORT
adb connect TV_IP:CONNECTION_PORT
adb devices
```

4. Open the extracted PC folder. On Windows run `HorizonX.cmd`; on Linux/macOS run `sh HorizonX.sh`. You can also run `python3 horizonx.py` (`py -3 horizonx.py` on Windows).
5. The assistant currently displays Spanish menus. Choose **1. Conectar televisor** (connect TV), then **2. Instalar HorizonX** (install). Enter **s** when asked whether to use HorizonX as Home. Press Home to verify.
6. **3. Optimizar** (optimize) is a separate option that shows its proposed changes before confirmation. It is not needed to follow the USB tutorial.

## Restore the original Home

In HorizonX, open **Settings → System → Back to the original Home**. This re-enables the original home screen. Android and its manufacturer functions are kept underneath HorizonX.

## Application name and update identity

The app and installer name is **HorizonX**. File managers may also show `tv.lightos`, its retained internal Android application ID. Existing Android updates must use the same application ID and compatible signing certificate. Renaming that ID would create a separate installation and needs a data migration. See [Android's update requirements](https://developer.android.com/google/play/app-updates).
