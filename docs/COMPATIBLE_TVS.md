# Compatible TVs

HorizonX has separate editions for Android TV/Google TV, Fire OS, LG webOS, Samsung Tizen, VIDAA and Roku. **LG has an IPK edition**; it does not use the Android APK. The operating system and firmware, not the brand alone, determine available features.

## Tested by us

| Model | System | Previously checked | Status |
|---|---|---|---|
| Philips Google TV TA7 (50PUD7908/43, PH3M_AL_T32) | Google TV 14 | Home, cleanup, volume and Continue watching | Earlier physical testing; no TV was connected during this review |

## By system

| System | Available installation | Main Home | HorizonX evidence |
|---|---|---|---|
| Android TV / Google TV, Android 8+ | Android APK + USB/ADB | Home picker, ADB or redirection, firmware-dependent | Philips TA7 tested; other brands are candidates, not certified |
| Fire TV running Android-based Fire OS 7/8 | Fire-specific APK + ADB assistant | Explicit boot and accessibility Home handling implemented; Amazon Home retained | Build and simulations; no physical Fire TV test |
| LG webOS | IPK + LG assistant | Persistent activities and optional native Home with existing root and compatible APIs | UI tested in official LG simulator; physical boot/Home/restore pending |
| Samsung Tizen | WGT + own Samsung signing certificates | Limited watcher, not certified native Home replacement | Browser and simulated tests |
| Roku OS | Development channel and screensaver | Does not replace Home | Built and tested in brs-engine |
| VIDAA Linux | Web app and community installer | Does not replace Home | Browser/installer tests; installation may be blocked by firmware |
| Amazon Vega | No published installable package | No verified integration | Does not run the Fire OS APK |

[Downloads, requirements and platform-specific steps](OTRAS_PLATAFORMAS.md).

Philips Titan OS/Saphi, Samsung Tizen, LG webOS and Roku cannot run Android APKs. A Hisense TV may use Google TV, Fire OS, VIDAA or Roku: check the OS before downloading. No new firmware is installed and other systems are not converted into Android. Root/administration methods are considered only for specific versions, with restoration.

## TVs with a clean-up profile (252)

Profiles derived from CleanYourTV (MIT). An exact match (same firmware) uses its own list; otherwise only components disabled without problems on many models are used.

- **TCL** (57): `tcl-32l5a`, `tcl-32s5400a`, `tcl-32s5k`, `tcl-40s5400a`, `tcl-43c645`, `tcl-43ep660`, `tcl-43p615`, `tcl-43s450f-ca`, `tcl-43s5400a`, `tcl-43s5k`, `tcl-50c725k`, `tcl-50dp660`, `tcl-50ep680`, `tcl-50p615`, `tcl-50p735`, `tcl-55c715`, `tcl-55c725`, `tcl-55c745`, `tcl-55c7k-uk`, `tcl-55c815`, `tcl-55ep640`, `tcl-55p638`, `tcl-55p7k`, `tcl-55p8ls`, `tcl-55s470g`, `tcl-55s546-us`, `tcl-58s571f-fire-tv`, `tcl-65c725`, `tcl-65c735`, `tcl-65c7k-google-tv`, `tcl-65c7l-google-tv`, `tcl-65q550g`, `tcl-65q650g`, `tcl-85rm7l-google-tv`, `tcl-ak30a5`, `tcl-beyondtv`, `tcl-beyondtv-pl`, `tcl-beyondtv-rt2851`, `tcl-beyondtv2-android-11`, `tcl-beyondtv2-latin-america`, `tcl-c755-google-tv`, `tcl-c845x2-google-tv`, `tcl-c89b-google-tv`, `tcl-g03-google-tv`, `tcl-g05-google-tv`, `tcl-g07-google-tv`, `tcl-g08-au-android12`, `tcl-g08-eu-android12`, `tcl-g08-us-google-tv`, `tcl-g09-google-tv`, `tcl-g10-google-tv`, `tcl-l40s66e`, `tcl-mt9655-cn-android14`, `tcl-q10g-pro`, `tcl-q7c-google-tv`, `tcl-qm6k-google-tv`, `tcl-uniontv-latin-america`
- **Sony** (32): `sony-bravia-4k-gb`, `sony-bravia-4k-gb-us`, `sony-bravia-4k-ur2`, `sony-bravia-4k-ur3`, `sony-bravia-4k-vh1`, `sony-bravia-4k-vh2`, `sony-bravia-4k-vh21`, `sony-bravia-4k-vh21-eu`, `sony-bravia-9-ii`, `sony-bravia-ae1`, `sony-bravia-ae2`, `sony-bravia-bf1`, `sony-bravia-tl2`, `sony-bravia-vu31`, `sony-kd-43x80l`, `sony-kd-49x8307c`, `sony-kd-55x8000c`, `sony-kd-55x8509c`, `sony-kd-55x85j`, `sony-kd-55xe8596`, `sony-kd-55xf7596`, `sony-kd-55xf8096`, `sony-kd-65x80j`, `sony-kd-65x82l`, `sony-kd-65x9300d`, `sony-x9000h-cn`, `sony-xbr-55x850c`, `sony-xbr-55x850d`, `sony-xbr-65x900f`, `sony-xbr-x900e`, `sony-xr-65a80j`, `sony-xr-65x90j-cn`
- **Xiaomi** (31): `redmi-mitv-antl0`, `redmi-mitv-mftp0`, `xiaomi-mi-box-3`, `xiaomi-mi-box-s`, `xiaomi-mi-box-s-2nd-gen`, `xiaomi-mi-tv-4a`, `xiaomi-mitv-aesp0`, `xiaomi-mitv-afmu0`, `xiaomi-mitv-afmu1`, `xiaomi-mitv-ansp0`, `xiaomi-mitv-astp0`, `xiaomi-mitv-astp1`, `xiaomi-mitv-astr0`, `xiaomi-mitv-axfr1`, `xiaomi-mitv-axso0`, `xiaomi-mitv-axso2`, `xiaomi-mitv-ayfr0`, `xiaomi-mitv-mffu0`, `xiaomi-mitv-mftr0`, `xiaomi-mitv-moeu0`, `xiaomi-mitv-mooq0`, `xiaomi-mitv-mooq2`, `xiaomi-mitv-moor2`, `xiaomi-mitv-mosr4`, `xiaomi-mitv-mssp0`, `xiaomi-mitv-mssp1`, `xiaomi-mitv-mssp2`, `xiaomi-mitv-mssp3`, `xiaomi-mitv-mssp3-android9`, `xiaomi-mitv-mteq0`, `xiaomi-tv-a-pro-2026`
- **Philips** (12): `philips-50pud7406`, `philips-50pus8517`, `philips-55oled707`, `philips-55oled708`, `philips-55pus7503`, `philips-65pus8102`, `philips-65pus9435`, `philips-75pus8505`, `philips-google-tv-ta7`, `philips-r8g-google-tv`, `philips-smart-4k-google-tv`, `philips-tpm191e`
- **Hisense** (10): `hisense-65d62qh`, `hisense-e5q-pro`, `hisense-fire-tv-aftcibfbd1`, `hisense-hg9`, `hisense-hismarttv-a4`, `hisense-hismarttv-a4-android11`, `hisense-smarttv-4k-ffm`, `hisense-smarttv-4k-ffm-android11`, `hisense-smarttv-4k-ffm-lushan`, `hisense-u75-hengshan`
- **Skyworth** (8): `skyworth-65a3f`, `skyworth-7s60-a5`, `skyworth-8r40-k5c`, `skyworth-sw-22sa`, `skyworth-swtv-21ae`, `skyworth-swtv-22ae-fhd`, `skyworth-swtv-24ae-4k-nf`, `skyworth-swtv-24na-4k-nf`
- **Amazon** (7): `amazon-fire-tv-aftdec012e`, `amazon-fire-tv-afteu014`, `amazon-fire-tv-afttiff43`, `amazon-fire-tv-stick-4k-2018`, `amazon-fire-tv-stick-4k-2023`, `amazon-fire-tv-stick-4k-max-2021`, `amazon-fire-tv-stick-lite-2020`
- **Thomson** (4): `thomson-32he5800`, `thomson-43rt1055`, `thomson-sppl-4k-sw6h`, `thomson-t32rtl6000`
- **BenQ** (3): `benq-e55-735`, `benq-e55-750`, `benq-gv32`
- **Google** (3): `google-chromecast-gtv-4k`, `google-chromecast-gtv-hd`, `google-tv-streamer-4k-kirkwood`
- **OnePlus** (3): `oneplus-tv-cebu`, `oneplus-tv-dubai`, `oneplus-tv-y1`
- **Panasonic** (3): `panasonic-4ktv-0su`, `panasonic-4ktv-jup`, `panasonic-th-40hs550k`
- **XGIMI** (3): `xgimi-horizon-s-pro`, `xgimi-mogo-2`, `xgimi-mogo-3-pro`
- **Anker** (2): `anker-nebula-d2140`, `anker-nebula-d2426`
- **Byintek** (2): `byintek-t5-max`, `byintek-u4`
- **CHiQ** (2): `chiq-ai-pont`, `chiq-gtvu65`
- **FFalcon** (2): `ffalcon-65s585c-pro`, `ffalcon-r34a0-cn`
- **Formovie** (2): `formovie-laser-4k-hanlla`, `formovie-mprojm05`
- **Haier** (2): `haier-android-tv-dvb2k`, `haier-h32s80efx`
- **Hitachi** (2): `hitachi-65qledsm20`, `hitachi-cdh-le32smart21`
- **Kalley** (2): `kalley-43g200`, `kalley-r10g`
- **Motorola** (2): `motorola-mt4310`, `motorola-swtv-24ae-fhd`
- **Nokia** (2): `nokia-streaming-box-8000`, `nokia-streaming-box-8010`
- **NVIDIA** (2): `nvidia-shield-tv-2019`, `nvidia-shield-tv-pro-2019`
- **onn** (2): `onn-4k-plus-2025`, `onn-4k-streaming-box-2023`
- **Sharp** (2): `sharp-2t-c32gh3000i`, `sharp-aquos-tve21f`
- **Toshiba** (2): `toshiba-cosmos-android-tv`, `toshiba-fire-tv-aftha004`
- **Vu** (2): `vu-4k-lushan`, `vu-premium-fhd-43-hamamatsucho`
- **Aipro2k** (1): `aipro2k`
- **Aiwa** (1): `aiwa-ai-pont-sa`
- **Artel** (1): `artel-cvte-mt5863`
- **Caxium** (1): `caxium-58-realtek-rtk2851p`
- **Cecotec** (1): `cecotec-shandao`
- **Challenger** (1): `challenger-32t22bt`
- **Compac** (1): `compac-atv-r2`
- **Coocaa** (1): `coocaa-k3-pro-90p3d-max`
- **Dialog** (1): `dialog-viu-sei103dl`
- **Eko** (1): `eko-2k-google-tv-tennoji`
- **Epson** (1): `epson-ls800`
- **Freebox** (1): `freebox-player-pop`
- **Gadnic** (1): `gadnic-proj100w`
- **Grundig** (1): `grundig-kunyang`
- **Inclo** (1): `inclo-google-tv-4k`
- **Insignia** (1): `insignia-ns55f301na25`
- **Jmgo** (1): `jmgo-n1s-holan`
- **JVC** (1): `jvc-android-tv-menlo`
- **Karbonn** (1): `karbonn-swtv-20ae`
- **Kogan** (1): `kogan-gtvu65kg`
- **KTC** (1): `ktc-4k-smart-tv-hongkong`
- **Liberton** (1): `liberton-ltv-24h01at`
- **Lumio** (1): `lumio-vision-7`
- **Magcubic** (1): `magcubic-hy300-pro`
- **MTC** (1): `mtc-uk-2k-android-tv`
- **Noblex** (1): `noblex-shinjuku`
- **OK** (1): `ok-ai-pont-ikebukuro`
- **Peaq** (1): `peaq-ptv43aqu-5023c`
- **Polytron** (1): `polytron-2k-hayward`
- **Portronics** (1): `portronics-beem-470`
- **PRISM+** (1): `prismplus-q65-ultra-r10g`
- **RCA** (1): `rca-ai-pont`
- **Rocktek** (1): `rocktek-gb1`
- **Sankey** (1): `sankey-smart2ktvse`
- **Sanyo** (1): `sanyo-atv-r2`
- **Sber** (1): `sber-salute-tv-at30a6`
- **Stellamore** (1): `stellamore-t950s`
- **Super** (1): `super-general-cvte-t972`
- **Telesystem** (1): `telesystem-ont2hd`
- **Tivo** (1): `tivo-stream-4k`
- **Tornado** (1): `tornado-65ua1400e`
- **Turkcell** (1): `turkcell-tv-plus-4k-box-dv6069y`
- **Verizon** (1): `verizon-stream-tv`
- **Vidda** (1): `vidda-mt9653`
- **Vision** (1): `vision-2024vision43stv`
- **Wanbo** (1): `wanbo-x5-pro`
