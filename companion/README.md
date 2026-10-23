# HorizonX 3.4.0 · asistente ADB para PC

1. Descomprime todo el ZIP antes de ejecutar. Incluye `HorizonX-3.4.0.apk`.
2. Instala Python 3.10+ y Android Platform Tools. Añade ADB al PATH o deja
   `platform-tools/` junto a `horizonx.py`.
3. Windows: abre `HorizonX.cmd`. Linux/macOS: ejecuta `sh HorizonX.sh` desde esta
   carpeta. También sirve `python3 horizonx.py` (`py -3 horizonx.py` en Windows).
4. Elige 1 para conectar tu TV y 2 para instalar. Autoriza la depuración en la TV;
   confirma cambiar Inicio solo si lo deseas.

Si usas depuración inalámbrica con código, ejecuta primero `adb pair IP:PUERTO`
y `adb connect IP:PUERTO` con los dos puertos diferentes que muestra la TV.
Después vuelve al asistente. La guía explica ambos pasos.

Si descargaste o clonaste el repositorio completo, el asistente está en `companion/`
y la APK en `../dist/HorizonX-3.4.0.apk`. En el ZIP de PC, la APK está junto al asistente.
Los scripts son el asistente ADB; no incluyen el proyecto Android. No necesitas
Gradle, Android Studio, JDK ni compilar HorizonX. Este ZIP se ejecuta en el PC,
no en el televisor. Para USB solo necesitas descargar y copiar la APK.

Guía: https://github.com/2207juan/HorizonX/blob/main/docs/GUIA.md
