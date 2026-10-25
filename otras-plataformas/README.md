# Otras plataformas · Other platforms

Experimental: compiladas y probadas en emulador o navegador, **sin probar en televisores reales**. / Built and tested in an emulator or browser, **not yet tested on real TVs**.

Requisitos: Python 3.10+ en un PC de la misma red. Para saber qué tienes: `python3 detect.py`.

| Televisor | Carpeta | Cómo |
|---|---|---|
| **Samsung** (Tizen 2017+) | `samsung-tizen/` | Activa el modo desarrollador del TV y ejecuta `HorizonX-Samsung.sh` / `.cmd`. Pide iniciar sesión en tu cuenta Samsung para firmar la app. |
| **Fire TV** (Fire OS 7/8) | `fire-tv/` | Activa *Depuración ADB* y ejecuta `HorizonX-FireTV.sh` / `.cmd`. HorizonX se abre encima del inicio de Amazon. |
| **Roku** | `roku/` | Activa el modo desarrollador (Inicio ×3, Arriba ×2, Derecha, Izquierda, Derecha, Izquierda, Derecha) y ejecuta `HorizonX-Roku.sh` / `.cmd`. Es un canal: no reemplaza el inicio. |
| **Hisense / Toshiba VIDAA** | `hisense-vidaa/` | `sudo python3 horizonx_vidaa.py` y sigue los pasos en pantalla (DNS temporal). Método comunitario; puede no funcionar en firmware 2025. |

Cada asistente se puede deshacer desde su propio menú. / Each assistant can undo its changes from its own menu.
