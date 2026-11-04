# [HorizonX](https://webdesing-40d1a.web.app/)

Mejoras de rendimiento e interfaz para televisores.

[Español](README.md) · [English](README.en.md) · [Português](README.pt.md) · [Sitio web](https://webdesing-40d1a.web.app/)

Versión actual para Android TV / Google TV: **3.11.0** · compilación 56.

| Instalación | Descarga directa |
|---|---|
| TV / USB / Downloader | [Descargar APK · 3.11.0](https://github.com/2207juan/HorizonX/raw/refs/heads/main/dist/HorizonX-3.11.0.apk) |
| PC / ADB · incluye la APK | [Descargar instalador PC · 3.11.0](https://github.com/2207juan/HorizonX/raw/refs/heads/main/dist/HorizonX-PC-3.11.0.zip) |

[Comprobar integridad (SHA-256)](https://github.com/2207juan/HorizonX/raw/refs/heads/main/dist/HorizonX-3.11.0-SHA256SUMS)

## Aplicaciones que se despliegan con el mando

![Aplicaciones que se despliegan con el mando](docs/media/apps-es.gif)

Desde la fila de aplicaciones, pulsa ↑ o ↓ para desplegarlas. Usa las flechas para recorrerlas y Atrás para volver.

## Qué incluye

Inicio con aplicaciones instaladas, fondos que siguen la selección, tarjetas animadas, Biblioteca, reloj, clima, reproducción de música y controles de volumen. Algunas funciones dependen de los permisos, las aplicaciones y las APIs del televisor. El diseño Android existente se conserva.

En Ajustes → Inicio puedes elegir iconos de clima clásicos, en color o animados. Solo se anima el icono actual mientras Inicio está visible; el pronóstico permanece estático. El saludo aparece arriba y el clima debajo.

El acceso de sonido es exclusivamente un mezclador de volumen: icono real de cada aplicación, −, barra y +, sin tarjetas ni controles de reproducción duplicados. Arriba/abajo elige la app e izquierda/derecha ajusta su volumen; mantener la flecha repite el ajuste. Sin reproductores aparece un aviso breve. El widget musical separado tiene **anterior, reproducir/pausar y siguiente**; usa sesiones reales y puede recuperar una sesión pausada mediante MediaBrowser. Los ajustes de cada app terminan al cerrarla y no cambian el volumen general. Android puede pausar Spotify al reproducir YouTube por el enfoque de audio: no se fuerza reproducción simultánea. Requiere ADB autorizado y APIs compatibles del firmware: Android 8+ para reproductores Java y Android 9+ para efectos de sesión nativos. No se promete control universal de HDMI directo, DRM ni todos los fabricantes.

El fondo incluye **Animado, Paisaje y Tu foto**; se retiraron Aurora y Noche. El bucle de vídeo silencioso ocupa unos 109 KiB y se decodifica por hardware a 960×540/20 fps. Libera su decodificador cuando queda cubierto por una imagen o sales de Inicio. Si faltan capacidades de hardware, hay poca RAM, ahorro de energía o movimiento desactivado, utiliza el paisaje estático.

Explorar y Continuar viendo excluyen navegadores, aunque publiquen recomendaciones o sesiones multimedia. Continuar viendo usa reproducción real compartida por las apps, no visitas recientes. Las tarjetas se abren en su aplicación de origen. Para YouTube, las filas genéricas no se consideran suscripciones: solo se aceptan filas identificadas como tales o la API oficial con autorización. La integración OAuth de solo lectura está implementada y probada con respuestas simuladas; **falta configurar el cliente de HorizonX en Google Cloud y autorizar una cuenta real**, por lo que esta compilación todavía no sincroniza automáticamente tus suscripciones.

El marcador de fútbol solo sigue una coincidencia única con los dos equipos identificados en los metadatos de reproducción o en un reproductor visible. No adivina por país o canal ni muestra todos los partidos. Si la app no expone información suficiente o el proveedor de resultados no cubre el encuentro, el widget permanece oculto.

HorizonX no instala otro firmware. Mantiene Android y los servicios originales: HDMI, sonido, redes, tienda y funciones del fabricante. Instalar una aplicación y convertirla en el inicio principal son pasos distintos. En plataformas restringidas no se promete sustituir Home.

## Instalar Android por USB

1. Descarga [HorizonX-3.11.0.apk](https://github.com/2207juan/HorizonX/raw/refs/heads/main/dist/HorizonX-3.11.0.apk), cópiala al USB y conecta el USB a la TV.
2. Abre un administrador de archivos en la TV. Abre **tu unidad USB** y localiza la APK. El nombre de la unidad depende de tu pendrive.
3. Si Android lo pide, autoriza a ese administrador a instalar aplicaciones desconocidas. Pulsa **Instalar**; si HorizonX ya existe, aparecerá **Actualizar**. Conserva la instalación existente para mantener sus datos.
4. Abre HorizonX desde las aplicaciones. La instalación de la APK por sí sola no garantiza que Home cambie.
5. En Android TV con selector de inicio, entra en Ajustes → Aplicaciones predeterminadas / Inicio, elige HorizonX y confirma el uso permanente. El nombre del menú cambia según la TV. Android 6/7 se configura por esta ruta manual.
6. Si Google TV impone su inicio, abre HorizonX → Ajustes → Sistema → Configura HorizonX y sigue el proceso de depuración/autorizar conexión. En los televisores que permiten ADB local, acepta **Permitir siempre** y activa el inicio. Si no está disponible, utiliza el asistente de PC.
7. Comprueba Home desde una aplicación y un encendido normal antes de dar la activación por probada.

La depuración **no es necesaria para instalar la APK por USB**. Puede ser necesaria para activar Home, el indicador de volumen avanzado o cambios del sistema. No la desactives durante una operación ADB. No se garantiza que un puerto USB compartido mantenga el mismo comportamiento al activar depuración.

## Instalar Android desde PC / ADB

1. Descarga el [paquete PC](https://github.com/2207juan/HorizonX/raw/refs/heads/main/dist/HorizonX-PC-3.11.0.zip) y extráelo. Incluye la APK y el asistente; no hace falta compilar ni clonar el proyecto.
2. Instala Python 3.10+ y [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools); comprueba que `adb` esté disponible en la terminal.
3. En la TV: Ajustes → Sistema → Información. Pulsa siete veces Compilación, si todavía no eres desarrollador. En Opciones de desarrollador habilita la depuración que ofrece tu modelo.
4. TV y PC deben estar en la misma red. En depuración inalámbrica distingue el **puerto de vinculación** del **puerto de conexión**. Si la TV exige vincular, ejecuta `adb pair IP:PUERTO_DE_VINCULACION` e introduce el código que muestra la TV. No publiques ese código.
5. Ejecuta `HorizonX.cmd` en Windows o `sh HorizonX.sh` en Linux/macOS. Elige conectar y proporciona la IP y el puerto de conexión actuales; acepta la autorización en la TV. Luego elige instalar/configurar. Los pasos que cambian Home o paquetes se autorizan por separado.
6. Comprueba que Home abra HorizonX. Una instalación/actualización correcta no sustituye esta verificación.

Downloader también puede instalar la APK desde:

```text
https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-3.11.0.apk
```

## Activación, optimización y restauración

- La selección de Home conserva Android y las aplicaciones originales. Ambilight y funciones específicas del fabricante siguen perteneciendo al sistema de la TV.
- La optimización conserva su mecanismo de análisis, autorización, respaldo y restauración. **No aplica listas de paquetes importadas ni supone que una regla sirve para todas las marcas.** Tras retirar aquellas listas, no hay recomendaciones genéricas automáticas: el asistente de PC exige revisar una selección individual antes de autorizarla. La limpieza no deshabilita paquetes automáticamente ni marca un análisis sin cambios como optimización realizada. Un catálogo de modelos no demuestra qué servicio es prescindible.
- No se desinstalan paquetes esenciales por reconocer una marca. Mantén los respaldos del asistente en el PC; son específicos del dispositivo.
- Para volver al inicio anterior: HorizonX → Ajustes → Sistema → Volver al inicio original. Si no puedes abrir HorizonX, usa el apartado de restauración del mismo asistente y el respaldo de esa TV. No desinstales el único inicio operativo antes de restaurar el anterior.
- Una actualización firmada con la misma identidad conserva los datos. El identificador interno estable `tv.lightos` evita crear otra instalación; la etiqueta visible es HorizonX.
- Una APK no sustituye las pantallas protegidas de Google, Samsung, LG o del fabricante. Los permisos y controles avanzados varían por firmware.

## Compatibilidad y versiones antiguas

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

## Catálogo de televisores

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

## Instalar las otras ediciones

Cada carpeta de `otras-plataformas/` contiene **otro paquete para otro sistema operativo**. No instales todas las carpetas ni una APK en LG/Samsung.

| Sistema | Archivo y asistente | Requisitos / restauración |
|---|---|---|
| Fire OS | `otras-plataformas/amazon-fireos/installer/` · `HorizonX-FireTV.cmd` o `sh HorizonX-FireTV.sh` | ADB autorizado. `home-plan` prepara respaldo/token; `home-activate` requiere ese token. `home-restore` usa el respaldo. Root nativo opcional solo si ya existe y pasa las comprobaciones |
| LG webOS | `otras-plataformas/lg-webos/installer/` · `python3 horizonx_webos.py install --device NOMBRE --ipk ARCHIVO.ipk` | LG Developer Mode y [CLI oficial LG](https://webostv.developer.lge.com/develop/tools/cli-installation), dispositivo ya vinculado con `ares-setup-device` / `ares-novacom --getkey`. Luego `launch`. Developer Mode tiene límites de sesión. Integración Home avanzada: `home-plan`, `home-activate`, `home-restore`, solo con root existente y respaldo |
| Samsung Tizen | `otras-plataformas/samsung-tizen/installer/` · `python3 horizonx_tizen.py install --tv IP` | Developer Mode, Tizen Studio/SDB y certificados Samsung del propietario. El asistente firma el WGT. `uninstall` retira la app; desactiva antes el vigilante si lo activaste. La ruta nativa avanzada conserva su propio respaldo |
| Roku | `otras-plataformas/roku-os/installer/` · `python3 horizonx_roku.py install --roku IP` | Cuenta Roku, Developer Mode e instalador de desarrollo. Solicita contraseña de forma interactiva. Solo un canal de desarrollo a la vez. `remove` lo retira; el botón Home continúa siendo Roku |
| VIDAA | `otras-plataformas/hisense-vidaa/installer/` · `python3 horizonx_vidaa.py` | El asistente muestra las rutas compatibles con el firmware. Usa `--app-url URL` para una copia alojada; el servidor local debe seguir disponible mientras la TV lo necesite. Retira la app desde las opciones que permita tu TV |

Los ayudantes avanzados no incluyen exploits ni conceden root. Si faltan APIs, firma, permisos o un método de restauración comprobable, no dan la sustitución de Home por completada. Consulta `--help` antes de usar un asistente; no ejecutes un cambio privilegiado sin revisar su plan.

## Cómo están organizados los archivos

- `README.md`: guía en español. `README.en.md`: English. `README.pt.md`: português.
- `dist/`: APK Android y paquete PC actuales.
- `companion/`: asistente ADB interpretable y catálogos; estos scripts son necesarios para que funcione la instalación desde PC.
- `otras-plataformas/`: instaladores y paquetes propios de cada sistema. No son instalaciones duplicadas.
- `docs/media/`: capturas y vídeos.
- `licenses/`: textos de licencia de recursos independientes que siguen incluidos.
- `SHA256SUMS`: comprobaciones de integridad de los paquetes publicados.

Las carpetas del repositorio y los Markdown **no consumen RAM del televisor**: solo se instala su paquete correspondiente. Simplificar la documentación no acelera Android. No se publica el proyecto Android ni archivos de firma.

## Fuentes y recursos

Catálogo elaborado a partir de documentación oficial: [Android](https://developer.android.com/tools/releases/platforms), [LG: motores por año](https://webostv.developer.lge.com/develop/specifications/web-api-and-web-engine), [Samsung: grupos de modelos](https://developer.samsung.com/smarttv/develop/specifications/tv-model-groups.html), [Samsung: motores web](https://developer.samsung.com/smarttv/develop/specifications/web-engine-specifications.html), [Amazon: versiones Fire](https://developer.amazon.com/docs/fire-tv/fire-os-overview.html), [Roku: equipos antiguos](https://developer.roku.com/dev/docs/hardware), [VIDAA: guía técnica](https://www.vidaa.com/wp-content/uploads/2020/12/WebApp_Development_Guide_for_VIDAA.pdf).

Outfit conserva su [OFL](licenses/Outfit-OFL.txt); los recursos de audio Kenney conservan [CC0](licenses/Kenney-CC0.txt). Kotlin y las bibliotecas de compatibilidad Android conservan sus avisos en `licenses/`. Los datos de clima Open-Meteo y de catálogo TVmaze tienen sus condiciones de atribución y uso; se consultan en ejecución. Las marcas e imágenes de servicios pertenecen a sus titulares.

## Capturas

### Inicio y música

![Inicio y música](docs/media/horizonx-after-es.png)

### Todas las aplicaciones

![Todas las aplicaciones](docs/media/apps-es.png)

### Clima

![Clima](docs/media/weather-es.png)

### Audio por aplicación

![Audio por aplicación](docs/media/audio-es.png)

### Ajustes

![Ajustes](docs/media/settings-es.png)

### Indicador de volumen

![Indicador de volumen](docs/media/volume-es.png)

### Fondo animado

![Fondo animado](docs/media/wallpaper-es.png)
