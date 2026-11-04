# HorizonX

Mejoras de rendimiento e interfaz para televisores.

[Español](#español) · [English](#english) · [Português](#português) · [APK Android 3.11.0](dist/HorizonX-3.11.0.apk) · [Instalador PC / PC installer](dist/HorizonX-PC-3.11.0.zip)

## Español

![HorizonX · es](docs/media/horizonx-after-es.png)

[▶ Ver la app en funcionamiento](docs/media/demo-es.mp4)

![Ver la app en funcionamiento](docs/media/demo-es.gif)

<details>
<summary>Más capturas</summary>

![Clima](docs/media/weather-es.png)

![Audio por aplicación](docs/media/audio-es.png)

![Ajustes](docs/media/settings-es.png)

![Volumen](docs/media/volume-es.png)

![Fondo animado](docs/media/wallpaper-es.png)

</details>


### Qué incluye

Inicio con aplicaciones instaladas, fondos que siguen la selección, tarjetas animadas, Biblioteca, reloj, clima, reproducción de música y controles de volumen. Algunas funciones dependen de los permisos, las aplicaciones y las APIs del televisor. El diseño Android existente se conserva.

En Ajustes → Inicio puedes elegir iconos de clima clásicos, en color o animados. Solo se anima el icono actual mientras Inicio está visible; el pronóstico permanece estático. El saludo aparece arriba y el clima debajo.

El acceso de sonido es exclusivamente un mezclador de volumen: icono real de cada aplicación, −, barra y +, sin tarjetas ni controles de reproducción duplicados. Arriba/abajo elige la app e izquierda/derecha ajusta su volumen; mantener la flecha repite el ajuste. Sin reproductores aparece un aviso breve. El widget musical separado tiene **anterior, reproducir/pausar y siguiente**; usa sesiones reales y puede recuperar una sesión pausada mediante MediaBrowser. Los ajustes de cada app terminan al cerrarla y no cambian el volumen general. Android puede pausar Spotify al reproducir YouTube por el enfoque de audio: no se fuerza reproducción simultánea. Requiere ADB autorizado y APIs compatibles del firmware: Android 8+ para reproductores Java y Android 9+ para efectos de sesión nativos. No se promete control universal de HDMI directo, DRM ni todos los fabricantes.

El fondo incluye **Animado, Paisaje y Tu foto**; se retiraron Aurora y Noche. El bucle de vídeo silencioso ocupa unos 109 KiB y se decodifica por hardware a 960×540/20 fps. Libera su decodificador cuando queda cubierto por una imagen o sales de Inicio. Si faltan capacidades de hardware, hay poca RAM, ahorro de energía o movimiento desactivado, utiliza el paisaje estático.

Explorar y Continuar viendo excluyen navegadores, aunque publiquen recomendaciones o sesiones multimedia. Continuar viendo usa reproducción real compartida por las apps, no visitas recientes. Las tarjetas se abren en su aplicación de origen. Para YouTube, las filas genéricas no se consideran suscripciones: solo se aceptan filas identificadas como tales o la API oficial con autorización. La integración OAuth de solo lectura está implementada y probada con respuestas simuladas; **falta configurar el cliente de HorizonX en Google Cloud y autorizar una cuenta real**, por lo que esta compilación todavía no sincroniza automáticamente tus suscripciones.

El marcador de fútbol solo sigue una coincidencia única con los dos equipos identificados en los metadatos de reproducción o en un reproductor visible. No adivina por país o canal ni muestra todos los partidos. Si la app no expone información suficiente o el proveedor de resultados no cubre el encuentro, el widget permanece oculto.

HorizonX no instala otro firmware. Mantiene Android y los servicios originales: HDMI, sonido, redes, tienda y funciones del fabricante. Instalar una aplicación y convertirla en el inicio principal son pasos distintos. En plataformas restringidas no se promete sustituir Home.

### Compatibilidad y versiones antiguas

Revisión del código: **3 de noviembre de 2026**. Compatibilidad antigua revisada con herramientas; actualización ADB a 3.11.0, retorno con Home y volumen comprobados en Philips TA7 con Android 14. USB y primera instalación desde cero siguen pendientes.

| Sistema | Versiones contempladas por el código | Instalación | Encender / Home | Comprobación disponible |
|---|---|---|---|---|
| Android TV / Google TV | Android **6, 7, 7.1, 8, 8.1, 9, 10, 11, 12, 12L, 13, 14, 15 y 16**; API 23–36 | APK Android | Selector de inicio; ADB cuando el firmware lo permite. Android 6/7 usa selección manual | Compilación y revisión de APIs con mínimo 23; actualización ADB 3.11.0 y Home probados en Philips TA7 / Android 14 |
| Amazon Fire OS | **6, 7, 8**; nuevas familias 14/16 según API Android instalada | APK Fire específica | Arranque y redirección de Home con accesibilidad; dependen del firmware. Activación separada y reversible | Compilación y simulaciones; sin TV Fire física |
| LG webOS | **3.x, 4.x, 5.x, 6.x, 22, 23, 24, 25, 26** | IPK LG | Integración avanzada experimental solo con root ya disponible y APIs comprobadas; instalar por Developer Mode no sustituye Home | Paquete y pruebas de navegador; prueba previa de interfaz en simulador oficial LG; Home físico pendiente |
| Samsung Tizen | **2.3, 2.4, 3.0, 4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 8.0, 9.0, 10.0** | WGT firmado con certificados del propietario | Vigilante limitado; la alternativa nativa exige root existente y comprobaciones. No equivale a sustitución universal de Home | Paquete, sintaxis ES5, navegador y simulaciones; sin TV Samsung física |
| Roku OS | **9.1 o posterior** como canal; modelos antiguos identificados en el catálogo | ZIP de desarrollo, canal + salvapantallas | **No sustituye Home**. Apertura de otros canales desde PC mediante ECP, cuando se permite | Compilación BrightScript y emulación; sin Roku físico |
| Hisense VIDAA | Motores Chromium 53 o posteriores, incluidos equipos documentados de 2016–2017 | Aplicación web por URL; depende del firmware | **No sustituye Home**. Puede necesitar un servidor para alojar la aplicación | Pruebas web e instalador simulado; hardware pendiente |

Las versiones son objetivos de compatibilidad del código, no una certificación de todos los modelos. Comprueba el **sistema instalado**, no solamente la marca o el año. Un Hisense puede tener VIDAA, Android, Google TV, Fire OS o Roku; cada uno usa su paquete correspondiente.

Fuera del mínimo: Android 5.x/API 22 e inferiores y Fire OS 5; LG NetCast y webOS 1/2; Samsung Orsay anterior a Tizen; Roku con firmware 3.1. Vega OS de Amazon no ejecuta APK Android y no tiene una edición instalable verificada aquí.

En Android 6/7 se incluyen bibliotecas de fechas compatibles y fuentes estáticas. En equipos que Android identifica con poca RAM se reduce la caché de imágenes; no se cambian las animaciones ni el diseño. Los proveedores de contenido introducidos en Android 8 y el puente de volumen/perfil que exige Android 8 no se fuerzan en sistemas anteriores. Las funciones que requieran esas APIs quedan limitadas; la navegación y las aplicaciones conservan sus rutas disponibles. TLS, certificados, DRM y servicios externos de equipos antiguos también dependen del fabricante.

### Catálogo de televisores

[Catálogo completo por modelo, generación y fuente oficial](companion/profiles/device-support.json). Incluye grupos de modelos Samsung, modelos Roku antiguos, familias Fire y generaciones de LG/Android. Sus registros distinguen **documentado**, **candidato** y **prueba física anterior**; no son listas de aplicaciones que se deban borrar.

Ejemplos de equipos antiguos reconocidos:

| Familia / modelo | Sistema o límite documentado | HorizonX |
|---|---|---|
| Philips Google TV TA7 / 50PUD7908/43 | Android 14, API 34 | Prueba física anterior; conserva el diseño Android actual |
| LG OLED55B6P / OLED65B6P (2016), UJ6300 (2017) | webOS 3.0 / 3.5, Chromium 38 | [Especificación LG](https://www.lg.com/us/support/products/documents/B6_Series_Spec_Sheet_Updated_10112016.pdf); adaptación antigua pendiente de hardware |
| Samsung series JS/JU de 2015 | Tizen 2.3 / WebKit | Candidato WGT; no se certifica el vigilante ni Home |
| Fire TV Stick 4K de 2018, AFTMM | Fire OS 6, API 25 | Candidato a APK Fire |
| Fire TV Stick 2.ª generación, AFTT | Fire OS 5, API 22 | Fuera del mínimo de esta APK |
| Roku 2 HD/XS, 3000X/3100X | Hasta Roku OS 9.1 | Candidato como canal; nunca reemplazo de Home |
| Roku 1/SE y Stick, 2710X/3500X | Hasta Roku OS 11 | Candidato como canal; nunca reemplazo de Home |
| Roku DVP / N1000 | Hasta Roku OS 3.1 | No compatible con esta edición |

Consulta local sin encender ni conectar una TV:

```sh
cd companion
python3 -m horizonx.support android-tv --sdk 23
python3 -m horizonx.support android-tv --sdk 33
python3 -m horizonx.support lg-webos --version 3.0
python3 -m horizonx.support samsung-tizen --version 2.3
python3 -m horizonx.support roku-os --version 9.1 --model 3100X
```

### Instalar Android por USB

1. Descarga [HorizonX-3.11.0.apk](dist/HorizonX-3.11.0.apk), cópiala al USB y conecta el USB a la TV.
2. Abre un administrador de archivos en la TV. Abre **tu unidad USB** y localiza la APK. El nombre de la unidad depende de tu pendrive.
3. Si Android lo pide, autoriza a ese administrador a instalar aplicaciones desconocidas. Pulsa **Instalar**; si HorizonX ya existe, aparecerá **Actualizar**. Conserva la instalación existente para mantener sus datos.
4. Abre HorizonX desde las aplicaciones. La instalación de la APK por sí sola no garantiza que Home cambie.
5. En Android TV con selector de inicio, entra en Ajustes → Aplicaciones predeterminadas / Inicio, elige HorizonX y confirma el uso permanente. El nombre del menú cambia según la TV. Android 6/7 se configura por esta ruta manual.
6. Si Google TV impone su inicio, abre HorizonX → Ajustes → Sistema → Configura HorizonX y sigue el proceso de depuración/autorizar conexión. En los televisores que permiten ADB local, acepta **Permitir siempre** y activa el inicio. Si no está disponible, utiliza el asistente de PC.
7. Comprueba Home desde una aplicación y un encendido normal antes de dar la activación por probada.

La depuración **no es necesaria para instalar la APK por USB**. Puede ser necesaria para activar Home, el indicador de volumen avanzado o cambios del sistema. No la desactives durante una operación ADB. No se garantiza que un puerto USB compartido mantenga el mismo comportamiento al activar depuración.

### Instalar Android desde PC / ADB

1. Descarga el [paquete PC](dist/HorizonX-PC-3.11.0.zip) y extráelo. Incluye la APK y el asistente; no hace falta compilar ni clonar el proyecto.
2. Instala Python 3.10+ y [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools); comprueba que `adb` esté disponible en la terminal.
3. En la TV: Ajustes → Sistema → Información. Pulsa siete veces Compilación, si todavía no eres desarrollador. En Opciones de desarrollador habilita la depuración que ofrece tu modelo.
4. TV y PC deben estar en la misma red. En depuración inalámbrica distingue el **puerto de vinculación** del **puerto de conexión**. Si la TV exige vincular, ejecuta `adb pair IP:PUERTO_DE_VINCULACION` e introduce el código que muestra la TV. No publiques ese código.
5. Ejecuta `HorizonX.cmd` en Windows o `sh HorizonX.sh` en Linux/macOS. Elige conectar y proporciona la IP y el puerto de conexión actuales; acepta la autorización en la TV. Luego elige instalar/configurar. Los pasos que cambian Home o paquetes se autorizan por separado.
6. Comprueba que Home abra HorizonX. Una instalación/actualización correcta no sustituye esta verificación.

Downloader también puede instalar la APK desde:

```text
https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-3.11.0.apk
```

### Activación, optimización y restauración

- La selección de Home conserva Android y las aplicaciones originales. Ambilight y funciones específicas del fabricante siguen perteneciendo al sistema de la TV.
- La optimización conserva su mecanismo de análisis, autorización, respaldo y restauración. **No aplica listas de paquetes importadas ni supone que una regla sirve para todas las marcas.** Tras retirar aquellas listas, no hay recomendaciones genéricas automáticas: el asistente de PC exige revisar una selección individual antes de autorizarla. La limpieza no deshabilita paquetes automáticamente ni marca un análisis sin cambios como optimización realizada. Un catálogo de modelos no demuestra qué servicio es prescindible.
- No se desinstalan paquetes esenciales por reconocer una marca. Mantén los respaldos del asistente en el PC; son específicos del dispositivo.
- Para volver al inicio anterior: HorizonX → Ajustes → Sistema → Volver al inicio original. Si no puedes abrir HorizonX, usa el apartado de restauración del mismo asistente y el respaldo de esa TV. No desinstales el único inicio operativo antes de restaurar el anterior.
- Una actualización firmada con la misma identidad conserva los datos. El identificador interno estable `tv.lightos` evita crear otra instalación; la etiqueta visible es HorizonX.
- Una APK no sustituye las pantallas protegidas de Google, Samsung, LG o del fabricante. Los permisos y controles avanzados varían por firmware.

### Instalar las otras ediciones

Cada carpeta de `otras-plataformas/` contiene **otro paquete para otro sistema operativo**. No instales todas las carpetas ni una APK en LG/Samsung.

| Sistema | Archivo y asistente | Requisitos / restauración |
|---|---|---|
| Fire OS | `otras-plataformas/amazon-fireos/installer/` · `HorizonX-FireTV.cmd` o `sh HorizonX-FireTV.sh` | ADB autorizado. `home-plan` prepara respaldo/token; `home-activate` requiere ese token. `home-restore` usa el respaldo. Root nativo opcional solo si ya existe y pasa las comprobaciones |
| LG webOS | `otras-plataformas/lg-webos/installer/` · `python3 horizonx_webos.py install --device NOMBRE --ipk ARCHIVO.ipk` | LG Developer Mode y [CLI oficial LG](https://webostv.developer.lge.com/develop/tools/cli-installation), dispositivo ya vinculado con `ares-setup-device` / `ares-novacom --getkey`. Luego `launch`. Developer Mode tiene límites de sesión. Integración Home avanzada: `home-plan`, `home-activate`, `home-restore`, solo con root existente y respaldo |
| Samsung Tizen | `otras-plataformas/samsung-tizen/installer/` · `python3 horizonx_tizen.py install --tv IP` | Developer Mode, Tizen Studio/SDB y certificados Samsung del propietario. El asistente firma el WGT. `uninstall` retira la app; desactiva antes el vigilante si lo activaste. La ruta nativa avanzada conserva su propio respaldo |
| Roku | `otras-plataformas/roku-os/installer/` · `python3 horizonx_roku.py install --roku IP` | Cuenta Roku, Developer Mode e instalador de desarrollo. Solicita contraseña de forma interactiva. Solo un canal de desarrollo a la vez. `remove` lo retira; el botón Home continúa siendo Roku |
| VIDAA | `otras-plataformas/hisense-vidaa/installer/` · `python3 horizonx_vidaa.py` | El asistente muestra las rutas compatibles con el firmware. Usa `--app-url URL` para una copia alojada; el servidor local debe seguir disponible mientras la TV lo necesite. Retira la app desde las opciones que permita tu TV |

Los ayudantes avanzados no incluyen exploits ni conceden root. Si faltan APIs, firma, permisos o un método de restauración comprobable, no dan la sustitución de Home por completada. Consulta `--help` antes de usar un asistente; no ejecutes un cambio privilegiado sin revisar su plan.

### Cómo están organizados los archivos

- `README.md`: esta única guía pública, en español e inglés.
- `dist/`: APK Android y paquete PC actuales.
- `companion/`: asistente ADB interpretable y catálogos; estos scripts son necesarios para que funcione la instalación desde PC.
- `otras-plataformas/`: instaladores y paquetes propios de cada sistema. No son instalaciones duplicadas.
- `docs/media/`: capturas y vídeos.
- `licenses/`: textos de licencia de recursos independientes que siguen incluidos.
- `SHA256SUMS`: comprobaciones de integridad de los paquetes publicados.

Las carpetas del repositorio y los Markdown **no consumen RAM del televisor**: solo se instala su paquete correspondiente. Simplificar la documentación no acelera Android. No se publica el proyecto Android ni archivos de firma.

### Fuentes y recursos

Catálogo elaborado a partir de documentación oficial: [Android](https://developer.android.com/tools/releases/platforms), [LG: motores por año](https://webostv.developer.lge.com/develop/specifications/web-api-and-web-engine), [Samsung: grupos de modelos](https://developer.samsung.com/smarttv/develop/specifications/tv-model-groups.html), [Samsung: motores web](https://developer.samsung.com/smarttv/develop/specifications/web-engine-specifications.html), [Amazon: versiones Fire](https://developer.amazon.com/docs/fire-tv/fire-os-overview.html), [Roku: equipos antiguos](https://developer.roku.com/dev/docs/hardware), [VIDAA: guía técnica](https://www.vidaa.com/wp-content/uploads/2020/12/WebApp_Development_Guide_for_VIDAA.pdf).

Outfit conserva su [OFL](licenses/Outfit-OFL.txt); los recursos de audio Kenney conservan [CC0](licenses/Kenney-CC0.txt). Kotlin y las bibliotecas de compatibilidad Android conservan sus avisos en `licenses/`. Los datos de clima Open-Meteo y de catálogo TVmaze tienen sus condiciones de atribución y uso; se consultan en ejecución. Las marcas e imágenes de servicios pertenecen a sus titulares.

## English

![HorizonX · en](docs/media/horizonx-after-en.png)

[▶ Watch the app in action](docs/media/demo-en.mp4)

![Watch the app in action](docs/media/demo-en.gif)

<details>
<summary>More screenshots</summary>

![Weather](docs/media/weather-en.png)

![App volume](docs/media/audio-en.png)

![Settings](docs/media/settings-en.png)

![Volume](docs/media/volume-en.png)

![Animated wallpaper](docs/media/wallpaper-en.png)

</details>


Weather icons can be classic, colored or animated under Settings → Home. Only the current icon animates while Home is visible; forecast icons stay static. The greeting is above the weather.

The sound shortcut is a volume-only mixer: each app’s real icon, −, a track and +, without cards or duplicate playback controls. Up/down selects an app; left/right adjusts its volume, including held keys. With no players, it shows a brief notice. The separate music widget has **previous, play/pause and next**, using real sessions and MediaBrowser for paused-session recovery. Per-app adjustments end when the app closes and do not change master volume. Android audio focus may pause Spotify when YouTube plays; simultaneous playback is not forced. Authorized ADB and compatible firmware APIs are required: Android 8+ for Java players, Android 9+ for native session effects. HDMI passthrough, DRM and every manufacturer are not universally supported.

Wallpaper choices are **Animated, Landscape and Your photo**; Aurora and Night were removed. The silent video loop is about 109 KiB, hardware decoded at 960×540/20 fps. Its decoder is released when artwork covers it or Home goes into the background. Unsupported hardware, low-RAM devices, power saving or disabled motion use the static landscape.

Explore and Continue watching exclude browsers across preview, history and playback sources. Continue watching uses actual shared playback, not recently visited apps. Cards open their originating application. Generic YouTube recommendations are never labelled subscriptions: only explicit subscription rows or the authorized official API qualify. The read-only OAuth integration is implemented and tested against simulated responses; **HorizonX’s Google Cloud OAuth client and a real account’s consent still need configuring**, so this build does not automatically synchronize subscriptions yet.

The football widget follows only one fixture identified by both teams in actual playback metadata or a visible player. It never guesses by country or channel. Missing player information or scoreboard coverage keeps it hidden.


### Installation and older TVs

The existing Android design is preserved. HorizonX changes the home interface; it does not replace the operating system or firmware.

| Platform | Code compatibility target | Actual Home support |
|---|---|---|
| Android TV / Google TV | Android **6–16**, API 23–36, including 11/12/13/14 | Home selector or firmware-dependent ADB activation. Android 6/7 uses manual Home selection. ADB update to 3.11.0, Home and volume tested on Philips TA7 / Android 14; older versions have API/build checks, not hardware certification |
| Fire OS | Fire OS **6/7/8**; newer 14/16 families according to installed Android API | Separate Fire APK; boot/accessibility integration is firmware-dependent and not physically certified |
| LG webOS | **3.x through 26**: 3/4/5/6/22/23/24/25/26 | IPK; experimental advanced Home integration requires existing root and supported APIs. Developer Mode installation alone is not Home replacement |
| Samsung Tizen | **2.3–10.0**, documented 2015–2026 generations | Signed WGT; limited watcher. Native path requires existing root and strict probes. Universal Home replacement is not claimed |
| Roku OS | **9.1+** development channel and screensaver | **Does not replace Home**; other apps may be opened externally over ECP |
| VIDAA | Documented Chromium 53+ engines; firmware-dependent URL installation | Hosted web app; **does not replace Home** |

These are software targets, not certification of every listed television. Android below API 23, Fire OS 5/API 22, LG NetCast/webOS 1–2, Samsung Orsay and Roku OS 3.1 are outside the supported package targets. Amazon Vega OS does not run Android APKs.

The [official-source catalog](companion/profiles/device-support.json) contains model identifiers, generation/version mappings and evidence labels. Inspect the **installed OS/API**, since model years can be misleading after updates. Catalog recognition never authorizes disabling services.

### USB APK installation

1. Download the [Android APK](dist/HorizonX-3.11.0.apk), copy it to your USB drive and open the drive on the TV using a file manager.
2. Allow that file manager to install unknown apps if requested. Select **Install**, or **Update** if HorizonX is already installed. Keep the existing installation to preserve its data.
3. Open HorizonX. Select it under the TV's Default apps / Home settings if that selector is available. Older Android 6/7 uses this manual route.
4. If the OEM forces its own Home, use HorizonX → Settings → System → Set up HorizonX. Follow the debugging authorization steps. If local ADB is unavailable, use the PC assistant below.
5. Test Home from another app and a normal power-on. Installing/updating the APK alone does not prove Home activation.

USB installation itself does not need developer mode. Advanced Home/volume/system changes may require authorized debugging. Do not turn debugging off during an ADB transaction.

### PC / ADB installation

Download and extract the [PC package](dist/HorizonX-PC-3.11.0.zip); it includes the APK. Install Python 3.10+ and [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools). Enable the debugging option available on your TV under Developer options; enable Developer options by pressing Build seven times under Settings → System → About, if needed.

Connect both devices to the same network. With wireless debugging, pairing and connection ports are different: use `adb pair IP:PAIRING_PORT` only if pairing is required, then supply the connection address to the assistant. Accept the TV authorization. Run `HorizonX.cmd` on Windows or `sh HorizonX.sh` on Linux/macOS; choose connect, then install/configure. Home and package changes require separate authorization.

Updates keep the stable internal package identity `tv.lightos` to retain data. The visible app name is HorizonX. To restore: Settings → System → Back to the original Home, or the matching assistant/backup if HorizonX cannot be opened. Restore the original Home before removing the only working launcher.

### Other platforms

Use **only** your OS folder under `otras-plataformas/`. The folders contain distinct OS builds, not additional components that every TV needs. Commands and file locations are in the platform installation table above; every assistant supports `--help`.

LG requires LG Developer Mode, a paired device and the official LG CLI. Samsung requires Developer Mode and the owner's signing certificates. Roku uses the development channel installer and can hold only one development channel. VIDAA installation/hosting depends on the firmware. Fire requires authorized ADB; Home activation/restoration uses an explicit plan and token. No helper supplies an exploit or silently grants root.

### Optimization, verification and resources

Analysis, individual approval, backup and restoration remain available. Imported removal lists have been removed: there are **no generic automatic package-removal recommendations** in this release. Unknown dependencies stay enabled. Package optimisation is not applied automatically, and an unchanged audit is not marked as completed optimisation. Review each proposed change on the actual device; matching a model is not evidence that its services are expendable.

Offline build, API checks, browser tests and emulation are distinct from hardware tests. The ADB update to 3.11.0, Home return and volume overlay were physically checked on Philips TA7 / Android 14 on November 3. Fresh installation and USB installation are still untested; no USB storage was detected. Boot, Home, protected settings, Google accounts, DRM and advanced volume behavior on other models still require their hardware. The advanced volume/profile bridge requires Android 8+ APIs; older Android uses its available fallback routes. Old TVs can also have obsolete TLS/DRM or unavailable online services.

The repository's directories and Markdown files do not consume TV RAM; only the selected installation package does. The public documentation is consolidated here; app source/build projects and signing keys are not distributed. Required resource licenses remain under `licenses/`: [Outfit OFL](licenses/Outfit-OFL.txt), [Kenney CC0](licenses/Kenney-CC0.txt) and Android library notices. Runtime TVmaze and Open-Meteo data retain their respective attribution/use terms. Service artwork and trademarks belong to their owners.

## Português

![HorizonX · pt](docs/media/horizonx-after-pt.png)

[▶ Veja o aplicativo em funcionamento](docs/media/demo-pt.mp4)

![Veja o aplicativo em funcionamento](docs/media/demo-pt.gif)

<details>
<summary>Mais capturas</summary>

![Clima](docs/media/weather-pt.png)

![Volume por aplicativo](docs/media/audio-pt.png)

![Configurações](docs/media/settings-pt.png)

![Volume](docs/media/volume-pt.png)

![Fundo animado](docs/media/wallpaper-pt.png)

</details>

### Recursos

Tela inicial com os aplicativos instalados, Biblioteca, cartões animados, imagem de fundo que acompanha a seleção, relógio e clima com ícones clássicos, coloridos ou animados. O widget musical tem **anterior, reproduzir/pausar e próxima**. O painel de áudio separado serve somente para volume: escolha o aplicativo com cima/baixo e ajuste com esquerda/direita. Sem reprodutores, aparece um aviso breve. O ajuste independente não modifica o volume geral nem força áudio simultâneo contra as regras de foco do Android.

Fundos: **Animado, Paisagem e Sua foto**. O vídeo silencioso usa decodificação por hardware, ocupa aproximadamente 109 KiB e libera o decodificador quando fica coberto ou você sai da tela inicial. Em aparelhos sem recursos suficientes, usa a paisagem estática.

Explorar e Continuar assistindo excluem navegadores. Continuar assistindo usa reprodução real compartilhada pelos aplicativos, não visitas recentes. As recomendações gerais do YouTube não são tratadas como inscrições. A integração oficial somente para leitura está implementada e tem testes simulados, mas **ainda precisa do cliente OAuth do HorizonX no Google Cloud e da autorização de uma conta real** para sincronizar inscrições.

O placar acompanha somente uma partida identificada pelos dois times na reprodução real. Não mostra todos os jogos por instalar um aplicativo esportivo. Catálogos, resumos e reprises não iniciam acompanhamento; sem dados suficientes, o widget fica oculto.

### Instalação Android TV / Google TV

1. Baixe o [APK Android 3.11.0](dist/HorizonX-3.11.0.apk).
2. Por USB: copie o APK para sua unidade, abra pelo gerenciador de arquivos e escolha Instalar ou Atualizar. Uma atualização conserva os dados se tiver o mesmo identificador e assinatura.
3. Instalar o APK e escolher a tela inicial são etapas diferentes. Abra HorizonX → Configurações → Sistema → Configurar HorizonX. Alguns firmwares permitem o seletor de início; outros exigem ADB autorizado.
4. Pelo computador: extraia o [instalador PC](dist/HorizonX-PC-3.11.0.zip), instale Python 3.10+ e [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools), ative a depuração disponível na TV e aceite a autorização do computador. Execute `HorizonX.sh` no Linux/macOS ou `HorizonX.cmd` no Windows e siga o menu.
5. A otimização é opcional e exige análise, aprovação e cópia de segurança. Não existem listas genéricas de remoção automática verificadas para todas as marcas.
6. Para voltar, use Configurações → Sistema → Voltar ao início original ou a restauração do assistente PC. Não troque firmware nem remova serviços essenciais para instalar o launcher.

[Download direto do APK para Downloader](https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-3.11.0.apk).

### Plataformas e limites

| Sistema | Versões consideradas | Tela inicial | Validação |
|---|---|---|---|
| Android TV / Google TV | Android 6–16, API 23–36 | Seletor ou ADB conforme o firmware | Philips TA7 / Android 14: atualização, Home, volume e interface testados |
| Fire OS | 6/7/8; famílias 14/16 conforme a API instalada | Redirecionamento e inicialização dependem do firmware | Compilação e simulações; sem Fire TV física |
| LG webOS | 3.x–26 | IPK; início nativo experimental com root já existente e APIs compatíveis | Interface no simulador; Home físico pendente |
| Samsung Tizen | 2.3–10 | WGT; vigilante limitado não equivale à substituição universal de Home | Testes de navegador e simulações |
| Roku OS | 9.1+ | Canal de desenvolvimento; não substitui Home | Compilação e emulação |
| VIDAA | Chromium 53+ | Aplicativo web; não substitui Home | Testes web e do instalador |

As versões são alvos do código, não certificação de todos os modelos. Uma marca pode usar sistemas diferentes. Escolha o pacote pelo sistema instalado. As edições separadas estão em [`otras-plataformas/`](otras-plataformas/). Nenhuma ferramenta fornece root ou uma vulnerabilidade para desbloquear a TV.

HorizonX mantém Android e as funções originais: HDMI, som, Wi-Fi, Bluetooth, loja e recursos do fabricante. O diretório do repositório e seus documentos não ocupam RAM na TV. O código Android, o projeto de compilação e as chaves de assinatura não são distribuídos aqui. Licenças necessárias dos recursos permanecem em `licenses/`.
