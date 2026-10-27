# Otras plataformas · Other platforms

Actualizado / Updated: **2026-10-26**. No se ha conectado ningún televisor en esta revisión. / No TV was connected during this review.

## Español

HorizonX no cambia Android, webOS, Tizen, VIDAA o Roku OS por otro sistema operativo. Cambia la interfaz de inicio cuando los permisos y el firmware lo permiten. **No admitir APK no equivale a no tener una edición HorizonX.**

| Sistema | Paquete | Estado del inicio principal |
|---|---|---|
| Android TV / Google TV | APK Android | Probado previamente en Philips TA7. Otras marcas y firmwares requieren comprobaciones propias. |
| LG webOS | [IPK y asistente](../otras-plataformas/lg-webos/README.md) | Interfaz comprobada en simulador oficial LG. Home y arranque avanzados implementados para root ya disponible y APIs admitidas; pendientes de prueba física. |
| Amazon Fire OS 7/8 | [APK Fire específica y asistente ADB](../otras-plataformas/amazon-fireos/README.md) | Receptor de arranque y retorno Home por accesibilidad implementados. Sin prueba física en Fire TV; no se deshabilita Amazon Home. |
| Samsung Tizen | [WGT y asistente de firma](../otras-plataformas/samsung-tizen/README.md) | Interfaz y vigilante probados con navegador/simulaciones. Vigilante limitado; no se certifica Home nativo. |
| Roku | [Canal y salvapantallas](../otras-plataformas/roku-os/README.md) | Compilado y probado en brs-engine. No sustituye Home. |
| VIDAA Linux | [Sitio web e instalador](../otras-plataformas/hisense-vidaa/README.md) | Interfaz probada en navegador. Instalación comunitaria dependiente del firmware; no sustituye Home. |
| Amazon Vega | Sin paquete publicado | No ejecuta la APK Fire OS. Desarrollo independiente sin inicio principal verificado. |

### Descargar y ejecutar

Descarga **Code → Download ZIP**, descomprime el repositorio entero y conserva la estructura de carpetas. Los paquetes específicos y los scripts necesarios están en `otras-plataformas/`. Requisitos generales: Python 3.10+; cada sistema añade sus herramientas. Los comandos siguientes se ejecutan desde la carpeta descargada, en un PC, y muestran ayuda sin conectarse a ninguna TV.

```sh
python3 otras-plataformas/lg-webos/installer/horizonx_webos.py --help
python3 otras-plataformas/amazon-fireos/installer/horizonx_fire.py --help
python3 otras-plataformas/samsung-tizen/installer/horizonx_tizen.py --help
python3 otras-plataformas/roku-os/installer/horizonx_roku.py --help
python3 otras-plataformas/hisense-vidaa/installer/horizonx_vidaa.py --help
```

**LG:** instala [webOS CLI de LG](https://webostv.developer.lge.com/develop/tools/cli-installation), conecta Developer Mode siguiendo su guía y registra el dispositivo con `ares-setup-device`. Con tu nombre emparejado real:

```sh
python3 otras-plataformas/lg-webos/installer/horizonx_webos.py install --device NOMBRE --ipk otras-plataformas/lg-webos/installer/tv.horizonx.webos_0.1.2_all.ipk
python3 otras-plataformas/lg-webos/installer/horizonx_webos.py launch --device NOMBRE
```

Esto instala y abre la app, sin apropiarse de Home. La integración avanzada requiere **root ya obtenido**, SSH con clave y huella de host confiable, servicio de descubrimiento autorizado y firmware admitido. No se obtiene root ni se aplica un exploit:

```sh
python3 otras-plataformas/lg-webos/installer/horizonx_webos.py home-plan --host IP --backup respaldo-lg --native-home
python3 otras-plataformas/lg-webos/installer/horizonx_webos.py home-activate --host IP --backup respaldo-lg --approve TOKEN
python3 otras-plataformas/lg-webos/installer/horizonx_webos.py home-restore --host IP --backup respaldo-lg --approve TOKEN
```

`TOKEN` lo genera el plan. El plan solo lee y guarda el respaldo en el PC. `--native-home` es opcional y se rechaza si no puede leer/restaurar la asignación original o comprobar el compositor. **Restaurar antes de desinstalar.** Developer Mode no equivale a root y su caducidad puede retirar apps.

**Fire OS:** instala Android Platform Tools, habilita y autoriza ADB en la TV. Usa exclusivamente la edición Fire:

```sh
python3 otras-plataformas/amazon-fireos/installer/horizonx_fire.py install --tv IP
python3 otras-plataformas/amazon-fireos/installer/horizonx_fire.py home-plan --tv IP --backup respaldo-fire.json
python3 otras-plataformas/amazon-fireos/installer/horizonx_fire.py home-activate --tv IP --backup respaldo-fire.json --approve TOKEN
python3 otras-plataformas/amazon-fireos/installer/horizonx_fire.py home-restore --tv IP --backup respaldo-fire.json --approve TOKEN
```

Instalar y activar son pasos distintos. No se promete que las restricciones de cada firmware permitan el arranque; debe verificarse con Home, encendido, reposo y apps originales. La limpieza es opcional y separada.

**Samsung:** `python3 otras-plataformas/samsung-tizen/installer/horizonx_tizen.py` abre el asistente. Requiere modo desarrollador y certificados Samsung propios; `python3 -m pip install cryptography` instala la dependencia de firma. La WGT incluida está sin firmar. El vigilante se puede desactivar; su retorno depende de la información de visibilidad del firmware.

**Roku:** `python3 otras-plataformas/roku-os/installer/horizonx_roku.py` abre el asistente. Usa el modo desarrollador oficial. Solo cabe un canal de desarrollo a la vez; conservar otro canal implica preparar su reinstalación antes de sustituirlo. No confundir canal de desarrollo con root ni con reemplazo Home.

**VIDAA:** el asistente explica el método DNS comunitario. Su ejecución como servidor DNS necesita permisos de administrador en el **PC**, no root en la TV. No se ejecuta por abrir `--help`. Para uso independiente del PC hay que alojar la app web con `--app-url`; esto sigue sin sustituir Home.

### Root y compatibilidad

Un proyecto de root para un modelo/firmware antiguo no demuestra soporte universal de HorizonX. Antes de cambiar el inicio deben conocerse el modelo, versión, método de acceso, originales y recuperación. La búsqueda de nuevas integraciones continúa; solo se anunciará como implementado lo que exista en esta distribución.

### Opción avanzada: Home nativo Samsung con root previo

Esta opción es independiente del vigilante y **no está certificada en hardware HorizonX**. Solo contempla ARMv7 soft-float y estos firmwares exactos: `T-KSU2EDUABC-0090-2130.0`, `T-PTMDAKUC-0090-2130.0` y `T-KSU2EFAKUC-0090-1300.9`. Otros se rechazan. No obtiene root; requiere SSH root ya autorizado y huella de host confiable. Si faltan permisos o APIs, falla sin forzarlas.

Descarga el [adaptador ARM](../otras-plataformas/samsung-tizen/installer/HorizonX-Tizen-Native-0.1.0-armv7) y consulta su [SHA256 y ABI](../otras-plataformas/samsung-tizen/installer/HorizonX-Tizen-Native-0.1.0-armv7.json). No lo ejecutes en el PC. Instala primero la WGT firmada y desactiva el vigilante Home limitado en los ajustes HorizonX. Conserva acceso SSH y el respaldo para recuperar Samsung Home.

Copia el binario a almacenamiento persistente de la TV mediante tu conexión root existente, por ejemplo:

```sh
scp -p otras-plataformas/samsung-tizen/installer/HorizonX-Tizen-Native-0.1.0-armv7 root@IP:/opt/usr/horizonx-native-home
ssh root@IP chmod 700 /opt/usr/horizonx-native-home
```

Debe ser un archivo normal propiedad de root, modo 700 o 755, con el mismo SHA256 publicado. Sustituye `SHA256` y `IP`; el ejemplo usa el perfil The Frame. Para S90D el perfil es `s90d-tizen9-2130`; para U8000F, `u8000f-1300.9`.

```sh
python3 otras-plataformas/samsung-tizen/installer/horizonx_tizen_native.py home-plan --host IP --helper-sha256 SHA256 --profile frame-tizen9-2130 --backup respaldo-tizen.json
python3 otras-plataformas/samsung-tizen/installer/horizonx_tizen_native.py home-activate --host IP --helper-sha256 SHA256 --backup respaldo-tizen.json --approve TOKEN
python3 otras-plataformas/samsung-tizen/installer/horizonx_tizen_native.py home-restore --host IP --helper-sha256 SHA256 --backup respaldo-tizen.json --approve TOKEN
```

El plan lee originales, identidad, firmware y binario; no cambia Home. La activación escribe únicamente Home y valores tipados de arranque mediante sus APIs, con comprobación y rollback. **Restaurar antes de desinstalar**, y conservar el binario en la ruta persistente. No se instala supervisor de salud ni gesto de emergencia: si la interfaz falla, se necesita SSH/restauración. Un setter aceptado no prueba Home físico ni encendido.

### Opción root Fire OS

Para quien ya disponga de `su` autorizado, el plan admite `--native-root-su /data/local/tmp/gl/su` (o la ruta existente de su instalación). Activa/restaura con los mismos comandos y token anteriores. Intenta el setter nativo y comprueba el resolver; si el firmware lo ignora, revierte. No deshabilita Amazon ni adquiere root. Si root era temporal, hay que conservar una vía de recuperación para poder restaurar después de reiniciar. El éxito del resolver tampoco certifica la tecla Home física.

[Proyectos investigados, límites y evidencia](ROOT_Y_HOME.md).

## English

HorizonX does not replace Android, webOS, Tizen, VIDAA or Roku OS. It changes the home interface where permissions and firmware allow. **Not supporting APK files does not mean no HorizonX edition exists.**

LG has a separate IPK tested for UI/navigation in LG's official simulator. Advanced boot/Home integration requires existing root, authorized SSH, an authorized discovery service and supported APIs. Hardware validation remains pending. Fire OS has its own APK with explicit boot handling and accessibility redirection, also pending physical validation. Samsung currently uses a limited watcher. Roku is a channel/screensaver and VIDAA a web app; neither replaces native Home. Vega is separate from Android-based Fire OS.

Download **Code → Download ZIP**, extract the entire repository and keep its directory structure. Run the `--help` commands above from the downloaded folder on your PC. All five were checked offline; help never connects to a TV. Python 3.10+ is required. LG additionally needs the LG CLI and paired Developer Mode device; Fire needs Android Platform Tools/authorized ADB; Samsung requires your own signing certificates and `cryptography`; Roku requires Developer Mode.

The LG and Fire commands above separately install, create a read-only plan, activate with its approval token, and restore. Replace `NOMBRE` with your paired LG device name and `IP` with your TV address. Keep backups private and **restore before uninstalling**. LG Developer Mode is not root; expired sessions may remove sideloaded apps. Do not use the Fire-specific APK to update Android TV.

Samsung's unsigned WGT must be signed for your TV. Its visibility watcher is not a verified native Home assignment. Installing Roku replaces any existing sideloaded development channel; Home remains Roku's. VIDAA's DNS method is community/firmware-dependent and requires administrator rights on the **PC**, not TV root; a hosted `--app-url` removes the serving-PC dependency without replacing Home.

No new physical TV compatibility is certified. Root/exploit projects are evaluated for their exact models, firmware, functionality and recovery; they do not imply universal support. Installation, cold boot, standby wake, Home from other apps, original TV functions and restoration are separate acceptance tests.

### Advanced existing-root options

Samsung has an optional native API adapter separate from the limited watcher. The ARMv7 soft-float binary and SHA256 are linked above. It requires existing trusted root SSH, the exact listed firmware, an installed boot-eligible HorizonX, and complete original settings. It does not acquire root or use the SDK execution workaround. Disable the watcher first, keep the helper at the persistent `/opt/usr/horizonx-native-home` path, and use the plan/activate/restore commands above. Native Home/startup values are read back; no physical Home/boot certification is implied. There is no automatic health guardian yet: keep SSH and restore before uninstalling.

Fire OS `home-plan` optionally accepts `--native-root-su` with an already authorized absolute su path. It attempts native assignment without disabling Amazon. Ignored changes fail and roll back. Temporary root may disappear after reboot; retain recovery access.

[Reviewed projects and actual implementation limits](ROOT_Y_HOME.md).
