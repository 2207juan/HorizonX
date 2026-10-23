# Guía de HorizonX

## 1. Instalar desde un USB (sin PC)

1. Copia `HorizonX-3.4.0.apk` a un pendrive y conéctalo al televisor.
2. Abre un gestor de archivos (por ejemplo «Cx Explorador» o «File Commander») e instala la APK. Si pide permiso para instalar apps desconocidas, concédelo a ese gestor.
3. En el televisor: **Ajustes → Sistema → Información** y pulsa 7 veces **Compilación**. Después, en **Opciones de desarrollador**, activa **Depuración USB / Depuración ADB**.
4. Abre HorizonX. Cuando aparezca **«¿Permitir depuración?»**, marca **Permitir siempre** y acepta.
5. A partir de ahí HorizonX hace el resto sola: permisos, la barra de volumen propia, la optimización segura (telemetría, anuncios y demos de tienda) y **se pone como pantalla de inicio**. En Google TV aparta el inicio original sin borrarlo.

## 2. Con un PC (opcional)

Necesitas Python 3.10+ y [Platform Tools](https://developer.android.com/tools/releases/platform-tools) (descomprímelas dentro de la carpeta del asistente como `platform-tools/`). Haz doble clic en `HorizonX.sh` o `HorizonX.cmd`:

```
1. Conectar televisor        4. Deshacer optimización
2. Instalar HorizonX         5. Volver al inicio original
3. Optimizar                 6. ¿Es compatible mi televisor?
```

Antes de aplicar nada, la optimización muestra la lista completa. La copia para deshacerla se guarda en `~/.horizonx/optimizaciones/`.

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
