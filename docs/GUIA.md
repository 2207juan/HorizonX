# Guía de instalación de HorizonX 3.5.1

La APK es la aplicación para el televisor. El ZIP para PC es un asistente Python que envía esa misma APK mediante ADB; no es otra versión de HorizonX. No necesitas el código Android, compilar ni iniciar sesión en GitHub para descargar.

## 1. Instalar desde un USB

1. [Descarga HorizonX-3.5.1.apk](https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-3.5.1.apk) en un PC o teléfono y copia el archivo a un USB.
2. Conecta el USB al televisor y abre tu gestor de archivos. Selecciona tu unidad USB, busca la carpeta donde guardaste la APK y abre el archivo.
3. Pulsa **Instalar**. Si HorizonX ya estaba instalado, verás **Actualizar**. Si Android bloquea la instalación, abre los ajustes de ese aviso, permite instalar desde ese gestor y vuelve al archivo.
4. Confirma la instalación en la ventana de Android y pulsa **Abrir** al terminar.
5. En HorizonX, abre el **engranaje de Ajustes → Sistema → Configurar HorizonX**.
6. Pulsa **Información del televisor**. Selecciona **Compilación** y pulsa OK siete veces. Si las opciones de desarrollador ya estaban habilitadas, continúa.
7. Vuelve a **Configurar HorizonX → Opciones de desarrollador** y deja activada **Depuración USB** o **Depuración ADB**, según tu modelo. No desactives la depuración si estás conectado desde un PC.
8. Vuelve a HorizonX y pulsa **Autorizar conexión ADB**. Si aparece **¿Permitir depuración?**, marca **Permitir siempre** y acepta.
9. En la misma pantalla, entra en **Usar HorizonX como inicio → Activar inicio**.
10. Pulsa **Home** en el mando, incluso desde otra aplicación, para comprobar que abre HorizonX.

[Vídeo completo en español](https://raw.githubusercontent.com/2207juan/HorizonX/main/docs/media/install-usb-es.mp4) · [Video in English](https://raw.githubusercontent.com/2207juan/HorizonX/main/docs/media/install-usb-en.mp4)

Instalar la APK y elegir Inicio son operaciones diferentes. La activación local requiere que el firmware exponga un ADB local y que el usuario lo autorice. Si HorizonX indica que no pudo activar el inicio, utiliza el asistente de PC del apartado siguiente. No hace falta borrar los datos ni desinstalar una versión anterior para actualizar.

Los botones **Información del televisor** y **Opciones de desarrollador** abren los paneles públicos de Android; evitan depender de la posición de esos ajustes en el menú de cada fabricante. El nombre exacto de Compilación y de la depuración puede variar.

## 2. Instalar con un PC por ADB

1. [Descarga el paquete ADB para PC](https://raw.githubusercontent.com/2207juan/HorizonX/main/dist/HorizonX-PC-3.5.1.zip) y descomprímelo. La carpeta **HorizonX-PC** ya incluye la APK; no copies el ZIP al televisor.
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
adb -s IP_TV:PUERTO install -r HorizonX-3.5.1.apk
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

## Identificador de actualización

El nombre público y de instalación es **HorizonX**. Algunos gestores de archivos muestran también `tv.lightos`, el identificador interno conservado para actualizar las instalaciones existentes sin crear una segunda app ni perder datos. Cambiar ese identificador exige una migración; no equivale a cambiar el nombre visible.
