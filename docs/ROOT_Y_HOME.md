# Root y Home: proyectos e integración · Root and Home integration

2026-10-26. Sin TV conectada / No TV connected. Los proyectos citados son referencias de terceros; no certifican nuestros paquetes en sus televisores.

## Español

Un launcher cambia la pantalla de inicio, no sustituye todo el sistema operativo. Root puede habilitar APIs que una app normal no puede usar, pero no garantiza compatibilidad de HorizonX, de cada firmware ni de los servicios originales.

### Implementado en esta actualización

- **Samsung:** adaptador nativo ARMv7 soft-float y controlador con perfiles exactos de firmware, SSH root previo, binario comprobado por SHA256, respaldo de Home/arranque, aprobación, lectura posterior y restauración. Son llamadas reales a APIs nativas; no depende del vigilante para asignar Home. **Sin prueba física** y sin supervisor de salud automático. Los ejemplos y requisitos están en [la guía](OTRAS_PLATAFORMAS.md).
- **Fire OS:** plan opcional con `--native-root-su`. Intenta asignación Home nativa usando root que el usuario ya tenga, sin deshabilitar Amazon. Si Fire ignora el setter, revierte. Conserva la activación/restauración del receptor y accesibilidad. Resolver correcto no demuestra la tecla física Home.
- **LG:** corregida la API canónica de asignación Home; IPK y asistente incluidos en la distribución. Las rutas root existentes y las comprobaciones físicas siguen separadas.
- **VIDAA:** callbacks nativos de mostrar/ocultar conectados al ciclo de vida, sin rediseñar la interfaz. No se afirma Home nativo.

### Referencias concretas

| Proyecto | Qué demuestra y qué límite conserva |
|---|---|
| [CleanFrame](https://github.com/nthnclrk/CleanFrame) | APIs nativas de Home en un The Frame y firmware concretos. No es instalador universal. |
| [Couchroot S90D](https://github.com/splitcipher/couchroot/blob/main/docs/lab/devices/s90d/README.md) | Operación Home y valores de arranque separados, con getters/setters tipados. Sus notas corrigen procedimientos antiguos de recuperación. |
| [AnthonMS Samsung](https://github.com/AnthonMS/samsung-tv-launcher) | Caso U8000F y bibliotecas de Tizen. Nuestra opción avanzada exige root existente y ABI/firmware comprobados. |
| [Clean Home Samsung](https://github.com/chaosmanage/samsung-tv-launcher) | Otra integración de APIs nativas. No se copió su mecanismo de ejecución. |
| [Clean Your TV LG](https://github.com/Razdva122/clean-your-tv-lg-webos) | Helpers locales, ediciones root/no-root y recuperación; compatibilidad por modelo/firmware y mando. |
| [Luma](https://github.com/ecklf/lg-luma) | Home nativo/OpenGL con montajes en algunas versiones. Su ejecutable no puede sustituirse simplemente por nuestro IPK web. |
| [Hearth](https://github.com/rudra-avatar/Hearth) | Home stand-in, montajes y recuperación; algunas versiones requieren reiniciar el gestor de aplicaciones. Esa ruta no se activa en HorizonX. |
| [GhostLock 5.10](https://github.com/R0rt1z2/GhostLock/tree/5.10) | Root para dispositivos/builds específicos, incluidos ciertos karat. No significa root en todo Fire OS. No se incluye ni ejecuta el exploit. |
| [Fire TV clean root](https://github.com/saisarathbb/firetv-clean-root) | Uso de root y Package Manager. No adoptamos sus promesas generales de latencia/compatibilidad ni modificaciones DRM. |
| [Kara standalone](https://github.com/Delitants/firetv-kara-standalone) | Perfil `kara/AFTKA`, build `0035334210436`; incluye cambios de Settings/tienda/teclado propios de su instalación. |
| [Mantis standalone](https://github.com/Delitants/firetv-mantis-standalone) | Perfil API 25 específico. Nuestra APK requiere API 26: root por sí solo no lo corrige. |
| [RootMyRoku](https://github.com/llamasoft/RootMyRoku) | Roku OS 9.4.0 build 4200 o anterior, chip Wi-Fi Realtek integrado. La cadena no funciona en OS 10 según sus autores. No demuestra sustitución actual de Home y bloquea comunicación con servidores Roku. |
| [Roku Dev Studio](https://github.com/paramount-engineering/roku-dev-studio) | Depuración y ECP; su consola de desarrollo no es shell Linux root ni reasignación Home. |
| [VIDAA clean TV](https://github.com/HALCONDEORO/vidaa-clean-tv) | Reducción de publicidad/ACR mediante configuración/DNS; no reemplaza Home. |
| [VIDAA launcher](https://github.com/Zfinix/vidaa-launcher) | Control mediante MQTT y un servidor externo. No demuestra un reemplazo autónomo sin ese servidor. |

**Roku no necesita que le conectes una tarjeta Wi-Fi:** el proyecto recordado depende de su chip integrado y del sistema antiguo. No se anuncia soporte de Home en Roku modernos basándose en ese jailbreak.

### Qué se ha comprobado

Samsung: binario compilado para ARM soft-float, 18 pruebas de transacción/guardas y 14 comprobaciones del C en host con bibliotecas simuladas. Fire: 24 pruebas de activación/restauración, incluyendo la ruta root. LG: 22 pruebas del instalador, además de interfaz en navegador y SDK oficial de aplicaciones. Estas pruebas no simulan íntegramente el sistema operativo ni sustituyen hardware real.

Faltan por dispositivo/firmware: instalación, encendido, reposo, Home desde otras apps, funciones originales y restauración. No se ejecutó ningún cambio privilegiado ni se adquirió root en una TV. No se cambió el diseño Android.

## English

A launcher changes the home interface, not the operating system. Root can unlock APIs, but does not establish compatibility with every model, firmware or original service.

This update adds a **Samsung native API adapter** for selected ARMv7 soft-float firmware, using pre-existing trusted root SSH, a pinned binary, original Home/startup snapshots, explicit approval, readback and rollback. It does not use a watcher to assign native Home, but remains unverified on hardware and has no automatic health guardian. [Setup and recovery](OTRAS_PLATAFORMAS.md).

**Fire OS** optionally accepts an already authorized `--native-root-su` path. It attempts native assignment while keeping Amazon enabled; ignored changes fail and roll back. Resolver results are not physical Home-key evidence. **LG** includes the IPK/installer and corrected native setter. **VIDAA** receives proper native hide/show lifecycle handling without a redesign.

The projects in the table are third-party technical references, not HorizonX compatibility certification. Luma/Hearth mounts or app-manager restarts are not automatically transplanted to our web app. GhostLock and Kara/Mantis target exact devices/builds, and Mantis API 25 remains below our APK minimum. No DRM modifications or root exploits are bundled/executed.

**RootMyRoku** uses the integrated Realtek Wi-Fi chip on old Roku OS 9.4.0/build 4200 or earlier, not an external Wi-Fi card. Its authors say the chain breaks in OS 10; it also blocks Roku-server communication. It does not establish a modern native Home replacement. Roku Dev Studio is a development/debugging tool, and VIDAA MQTT setups require an external server.

Builds and simulated tests passed; native TV boot, standby wake, physical Home, original functions and restoration still need model/firmware-specific hardware tests. No TV was connected and no privileged TV changes were executed.
