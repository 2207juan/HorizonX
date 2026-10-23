# Guía de instalación de HorizonX 3.4.0

La APK es la aplicación para el televisor. El ZIP para PC es un asistente Python que envía esa misma APK mediante ADB; no es otra versión de HorizonX. No necesitas el código Android, compilar ni iniciar sesión en GitHub para descargar.

## 1. Instalar desde un USB (sin PC)

1. [Descarga el archivo HorizonX-3.4.0.apk](https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-3.4.0.apk). Guarda el archivo, no la página web. Cópialo a un pendrive y conéctalo al televisor.
2. Abre un gestor de archivos (por ejemplo «Cx Explorador» o «File Commander») e instala la APK. Si pide permiso para instalar apps desconocidas, concédelo a ese gestor.
3. En el televisor: **Ajustes → Sistema → Información** y pulsa 7 veces **Compilación**. Después, en **Opciones de desarrollador**, activa **Depuración USB / Depuración ADB**.
4. Abre HorizonX. Cuando aparezca **«¿Permitir depuración?»**, marca **Permitir siempre** y acepta.
5. En **Ajustes → Configura HorizonX**, sigue la configuración. Si el firmware permite su ADB local y lo has autorizado, esta versión intenta activar permisos, volumen, limpieza por modelo y Home. Puede apartar el launcher Google TV, sin borrar Android.

Instalar por USB solo instala la app: la selección de Inicio y los permisos son pasos adicionales. Depuración USB no garantiza que un modelo exponga el ADB local que necesita HorizonX. Si no aparece el permiso o no se completa la configuración, prueba el método PC. La instalación inicial en todos los modelos y el arranque posterior no están certificados. Sin acceso ADB puedes abrir HorizonX como aplicación normal.

## 2. Instalar con un PC por ADB

1. [Descarga el paquete ADB para PC](https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-PC-3.4.0.zip) y descomprímelo. La carpeta **HorizonX-PC** ya incluye la APK; no copies el ZIP al televisor.
2. Instala **Python 3.10+** y [Platform Tools oficiales de Android](https://developer.android.com/tools/releases/platform-tools). Añade ADB al PATH o deja `platform-tools/` junto a `horizonx.py`.
3. Activa la depuración del televisor. Autoriza este PC cuando Android lo solicite. PC y TV deben estar en la misma red si conectas por Wi-Fi.
4. En Windows ejecuta `HorizonX.cmd`. En Linux/macOS abre una terminal dentro de **HorizonX-PC** y ejecuta `sh HorizonX.sh`. También puedes usar `python3 horizonx.py` (`py -3 horizonx.py` en Windows).
5. Elige **1. Conectar televisor** y luego **2. Instalar HorizonX**. El asistente transfiere e instala la APK. La pregunta de usar HorizonX como Inicio es un paso posterior: acéptala si quieres sustituir la pantalla principal. No es necesario un USB para este método. Al terminar pulsa Home si elegiste HorizonX como Inicio, o ábrelo desde la lista de aplicaciones.

```
1. Conectar televisor        4. Deshacer optimización
2. Instalar HorizonX         5. Volver al inicio original
3. Optimizar                 6. ¿Es compatible mi televisor?
```

La opción separada **3. Optimizar** muestra los cambios antes de pedir aprobación. Guarda sus copias para restaurar en `~/.horizonx/optimizaciones/`. La app también tiene su propia configuración automática cuando autorizas su ADB local; esa autorización tiene efectos sobre permisos, Inicio y limpieza.

### Depuración inalámbrica con código de emparejamiento

En televisores que ofrecen **Depuración inalámbrica → Emparejar con código**, el puerto de emparejamiento es distinto al de conexión. Antes de abrir el menú del asistente, utiliza en la terminal:

```sh
adb pair IP_TV:PUERTO_EMPAREJAMIENTO
adb connect IP_TV:PUERTO_CONEXION
adb devices
```

Sustituye ambos marcadores por lo que muestra tu TV e introduce el código cuando ADB lo solicite. No escribas el código en un archivo. Comprueba que `adb devices` indique `device`. Después abre el asistente y elige Conectar; detectará el dispositivo autorizado.

Si dejaste Platform Tools dentro de esta carpeta en lugar de añadirlo al PATH, usa `./platform-tools/adb` en Linux/macOS o `.\platform-tools\adb.exe` en Windows. No supongas que el puerto sea 5555: úsalo solo si tu televisor realmente expone la conexión clásica en ese puerto. La conexión inalámbrica del PC y la conexión ADB local que intenta abrir HorizonX son funciones diferentes.

### Descargar el repositorio completo

**Code → Download ZIP** incluye `companion/` y `dist/`. Descomprime todo y ejecuta el asistente desde `companion/`; encontrará la APK en `../dist/`. También puedes clonarlo:

```sh
git clone https://github.com/2207juan/HorizonX.git
cd HorizonX/companion
python3 horizonx.py
```

El repositorio público contiene instaladores, no el proyecto privado del launcher. No hace falta clonar si descargaste el ZIP de PC.

### Instalar solo la APK mediante comandos ADB

Si ya tienes un dispositivo autorizado, puedes instalar manualmente:

```sh
adb -s IP_TV:PUERTO install -r HorizonX-3.4.0.apk
```

Ejecuta desde donde guardaste la APK y reemplaza `IP_TV:PUERTO` por el serial exacto de `adb devices`. Esta orden instala o actualiza la app; no concede por sí sola todos los permisos del asistente ni cambia automáticamente Home.

## 3. Usar HorizonX

- **Flechas**: moverse. **OK**: abrir. **Atrás**: volver a la fila de contenido.
- **Abajo** desde el contenido: tus apps. Si sigues bajando, se despliega la cuadrícula completa.
- **Mantener OK** sobre una app: moverla con las flechas. Pulsa OK para soltarla.
- **Engranaje, tecla Menú o botón de ajustes del mando**: ajustes rápidos.
- Ocultar, ver información o desinstalar una app: **Ajustes → Aplicaciones**.
- Fondo, nombre del saludo, clima, sonidos y TizenTube: **Ajustes → Apariencia**.

## 4. Deshacer todo

- **Optimización**: Ajustes → Sistema → **Deshacer la optimización**, o la opción 4 del asistente de PC.
- **Inicio original**: Ajustes → Sistema → **Volver al inicio original**, o la opción 5 del asistente.
- **Barra de volumen del sistema**: Ajustes → Sistema → desactiva **Volumen de HorizonX**.
- A mano por ADB: `adb shell pm enable --user 0 NOMBRE.DEL.PAQUETE`.

## 5. Límites conocidos

- Si el sonido sale por una barra de sonido HDMI ARC, el volumen lo gestiona la barra y se mantiene su indicador.
- En Philips/MediaTek, la barra propia necesita el ADB local. Si se desactiva la depuración, vuelve la barra del sistema.
- *Continuar viendo* de apps no oficiales (Xuper, Magis…) solo aparece si esa app publica su reproducción a Android.

## 6. Qué hace el comando de publicación del creador

El script privado `publish_public_distribution.sh` sube los instaladores a GitHub. **No instala nada en una TV.** Los usuarios descargan la APK o el paquete ADB con los enlaces anteriores; no necesitan ese script de publicación.
