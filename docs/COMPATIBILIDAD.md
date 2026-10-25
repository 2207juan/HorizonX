# Televisores compatibles

HorizonX funciona en **Android TV, Google TV y Fire OS**. Samsung, LG, VIDAA y Roku usan sistemas propios y no instalan APK.

## Probado por nosotros

| Modelo | Sistema | Comprobado | Estado |
|---|---|---|---|
| Philips Google TV TA7 (50PUD7908/43, PH3M_AL_T32) | Google TV 14 | Inicio, limpieza (22 componentes), animación de volumen, Continuar viendo | Funciona |

## Cualquier Android TV

HorizonX no depende de la marca: funciona en cualquier televisor o aparato con Android TV o Google TV desde Android 8. Al activar el inicio, primero solo se elige HorizonX (suficiente en la mayoría de marcas); si el launcher del fabricante sigue delante, HorizonX aparta únicamente los paquetes que Android declara como «inicio», uno a uno y con copia para deshacerlo. Si el fabricante no deja cambiar el inicio o no hay ADB, HorizonX se abre encima del inicio del televisor cada vez que este aparece (como en Fire TV). Ajustes → Sistema → «Volver al inicio original» lo deshace todo.

## Por sistema

| Sistema | APK | Limpieza | Reemplazar inicio | Animación de volumen |
|---|---|---|---|---|
| **Google TV (Android 10–14)**<br>Philips (TA7, R8G, 2023+), Sony Bravia (2021+), TCL (C/P/Q, 2021+), Hisense (Google TV), Xiaomi TV A/A Pro, Chromecast con Google TV, Google TV Streamer, onn 4K, Motorola, Kalley, Panasonic, Sharp, Toshiba (Google TV), Skyworth, Thomson, Hitachi, JVC, RCA, Aiwa, CHiQ, Kogan, Nokia Streaming Box, Tivo Stream 4K, Xgimi | Sí | Sí | Con ADB, o se abre sobre el inicio del televisor | Sí (con ADB en algunas marcas) |
| **Android TV (8–12, launcher clásico)**<br>Philips (2017–2022, org.droidtv), Sony Bravia (2015–2020), TCL (Android TV 9–11), Xiaomi Mi TV / Mi Box, NVIDIA Shield, Hisense (Android TV), Sharp Aquos, Toshiba, OnePlus TV, Realme, Haier, Vu, Nokia | Sí | Sí | Selector de inicio, ADB, o se abre sobre el inicio | Sí (con ADB en algunas marcas) |
| **Amazon Fire OS (Fire TV Stick, televisores Fire TV)**<br>Fire TV Stick (2018+), Fire TV Cube, Toshiba Fire TV, Hisense Fire TV, TCL Fire TV, Insignia Fire TV | Sí | Parcial | Sí (con ADB en algunas marcas) | Sí (con ADB en algunas marcas) |

## No compatibles por ahora

- **Samsung Tizen** (Samsung (todos los Smart TV desde 2015)): No ejecuta APK ni tiene ADB. Solo existe una API de mando por red (puertos 8001/8002) para pulsar teclas y lanzar apps. Mejora posible: desactivar anuncios y 'Información de visualización' en los menús y bloquear dominios de publicidad con DNS. Alternativa real: conectar un Chromecast/Google TV o Fire TV y usar HorizonX allí.
- **LG webOS** (LG (todos los Smart TV)): No ejecuta APK. Existen launchers web propios con Developer Mode (webos-vibehack) y limpieza solo con root (Homebrew Channel). Alternativa: un dispositivo Google TV por HDMI.
- **Hisense / Toshiba VIDAA (Linux)** (Hisense VIDAA U, Toshiba VIDAA) — ahora con versión experimental aparte (ver abajo): VIDAA OS no es Android. Ojo: algunos Hisense chinos llaman 'VIDAA' a una capa sobre Android 11 (MT9653); esos sí aparecen en la base de datos y aceptan ADB.
- **Roku OS** (Roku TV (TCL, Hisense, Sharp, onn con Roku), Roku Express/Stick): Solo control remoto por ECP (puerto 8060). Sin instalación de apps externas fuera del modo desarrollador de canales.
- **Otros sistemas cerrados** (Apple TV, Huawei Vision, Panasonic MHS, Philips Titan OS / Saphi, Whale OS (Zeasn)): Apple tvOS, Huawei HarmonyOS TV, Panasonic My Home Screen (Firefox OS), Titan OS (Philips/JVC económicos 2024+), Whale OS y Saphi no admiten APK. Philips con Titan OS o Saphi no son Android aunque sean de la misma marca.

## Otras plataformas (versiones aparte, sin probar en hardware)

| Sistema | Versión de HorizonX | Estado |
|---|---|---|
| Samsung Tizen 2017+ | App web + servicio que la reabre con Home (`samsung-tizen/`) | Compilada y probada en navegador |
| Fire TV con Fire OS 7/8 | La misma APK; se abre sobre el inicio de Amazon (`amazon-fireos/`) | Compilada; sin probar en Fire TV |
| Fire TV con Vega OS | Proyecto React Native (`amazon-vega/`) | Sin compilar (requiere el SDK de Amazon) |
| Roku | Canal + salvapantallas, no reemplaza el inicio (`roku-os/`) | Compilado y probado en emulador |
| Hisense / Toshiba VIDAA | App web (`hisense-vidaa/`) instalada con el método comunitario «vidaahub»; no reemplaza el inicio | Experimental: Hisense no lo permite oficialmente y en firmwares de 2025 puede estar bloqueado |
| LG webOS | — | No compatible por ahora |

## Televisores con perfil de limpieza (252)

Perfiles derivados de CleanYourTV (MIT). Con coincidencia exacta (mismo firmware) se usa su lista; si no, solo componentes deshabilitados sin problemas en muchos modelos.

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

## Notas

- **Philips**: Android/Google TV de TP Vision (org.droidtv.*) o fabricados por Skyworth/MOKA según región. Nunca deshabilitar org.droidtv, org.droidtv.icp, ambisvc (Ambilight) ni eum. En TA7 el botón de ajustes (scancode 357) depende de launcherx o del servicio de HorizonX.
- **Sony**: Conservar com.sony.dtv.tvinput.*, braviasync* (HDMI-CEC), remotepairing, tvx y todo com.mediatek.*. Samba TV (tv.samba.ssm) es seguimiento.
- **TCL**: Conservar com.tcl.tv, tvinput, suspension (menú de entradas), dashboard y autopair. com.tcl.bi y logkit son telemetría.
- **Xiaomi**: PatchWall: el botón Home envía KEYCODE_ALL_APPS. com.miui.analytics y csi son telemetría.
- **Hisense**: En Android, no tocar Smartsense/AIoT (hubo casos de Recovery). Los anuncios son com.hisense.service.ad y business.ad.
- **Amazon**: Fire OS: no tocar com.amazon.tv.launcher, firehomestarter ni ajustes.
- **Samsung**: Tizen: no compatible con la APK. Ver plataforma tizen.
- **LG**: webOS: no compatible con la APK. Ver plataforma webos.
