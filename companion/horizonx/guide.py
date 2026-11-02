"""Guided menu for people who never used ADB: connect, install, optimise, restore.

Opened by double-clicking HorizonX.sh / HorizonX.cmd with no arguments. Every change asks first.
"""
from __future__ import annotations

import json
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from . import optimize
from .adb import Adb, Error

HERE = Path(__file__).resolve().parents[1]
STATE = Path.home() / ".horizonx" / "optimizaciones"


def ask(text: str) -> str:
    try:
        return input(text).strip()
    except EOFError:
        return "0"


def yes(text: str) -> bool:
    return ask(f"{text} [s/N]: ").lower() in ("s", "si", "sí", "y")


def adb_path() -> str:
    found = shutil.which("adb") or next((str(p) for p in HERE.glob("platform-tools/adb*")), None)
    if not found:
        raise Error("No encuentro ADB. Descarga «Android SDK Platform-Tools» de developer.android.com, "
                    "descomprímelo dentro de esta carpeta (platform-tools/) y vuelve a abrir HorizonX.")
    return found


def devices(adb: str) -> list[str]:
    out = subprocess.run([adb, "devices"], capture_output=True, text=True).stdout.splitlines()[1:]
    return [l.split()[0] for l in out if l.strip().endswith("device")]


def connect(adb: str) -> Adb | None:
    found = devices(adb)
    if len(found) == 1:
        print(f"Televisor conectado: {found[0]}")
        return Adb(found[0], adb)
    if len(found) > 1:
        for i, d in enumerate(found, 1):
            print(f"  {i}. {d}")
        pick = ask("Elige el número del televisor: ")
        return Adb(found[int(pick) - 1], adb) if pick.isdigit() and 0 < int(pick) <= len(found) else None
    print("\nEn el televisor: Ajustes > Sistema > Información > pulsa 7 veces «Compilación».\n"
          "Luego Opciones de desarrollador > activa «Depuración USB» (o «Depuración ADB»).\n"
          "La IP está en Ajustes > Red e Internet > tu Wi-Fi.")
    ip = ask("Escribe la IP del televisor (por ejemplo 192.168.1.20): ")
    if not ip:
        return None
    target = ip if ":" in ip else f"{ip}:5555"
    print(subprocess.run([adb, "connect", target], capture_output=True, text=True).stdout.strip())
    print("Si en la tele aparece «¿Permitir depuración?», marca «Permitir siempre» y pulsa Aceptar.")
    ask("Pulsa Enter cuando lo hayas aceptado... ")
    return Adb(target, adb) if target in devices(adb) else None


def describe(dev: dict) -> None:
    print(f"\n{dev['manufacturer']} {dev['model']} · Android {dev['android']} · {dev['platform']}")
    db = optimize.database()
    model, how = optimize.match_model(db, dev)
    print(f"Perfil exacto en la base de datos: {model['id']} ({how})" if model else
          "Sin perfil exacto: no se aplican recomendaciones automáticas de otros modelos.")


def select_apk():
    """Only the Android TV artifact; semantic versions, optional release hash verification."""
    candidates = []
    for folder in (HERE, HERE.parent / "dist"):
        for path in folder.glob("HorizonX-*.apk"):
            match = re.fullmatch(r"HorizonX-(\d+)\.(\d+)\.(\d+)\.apk", path.name)
            if match:
                candidates.append((tuple(map(int, match.groups())), path))
    if not candidates:
        raise Error("No encuentro una APK Android HorizonX-x.y.z.apk; la edición Fire OS no sirve para este asistente.")
    metadata = HERE / "release.json"
    release = json.loads(metadata.read_text()) if metadata.exists() else None
    if release:
        expected = f"HorizonX-{release['version']}.apk"
        paths = [path for _, path in candidates if path.name == expected]
        if not paths:
            raise Error("Falta la APK de esta distribución: " + expected)
        apk = paths[0]
        if hashlib.sha256(apk.read_bytes()).hexdigest() != release['apk_sha256']:
            raise Error("La APK no coincide con la suma de esta distribución; vuelve a descargar el paquete PC.")
    else:
        apk = max(candidates, key=lambda item: item[0])[1]
    return apk, release


def install(a: Adb) -> None:
    apk, release = select_apk()
    sdk = int(a.shell("getprop", "ro.build.version.sdk").strip())
    minimum = int((release or {}).get("min_sdk", 23))
    if sdk < minimum:
        raise Error(f"Esta APK requiere Android API {minimum}+; la TV tiene API {sdk}. No se modificó la TV.")
    print(f"Instalando {apk.name}...")
    print(a.command("install", "-r", str(apk), timeout=180))
    actual = a.shell("dumpsys", "package", "tv.lightos")
    if release and not re.search(r"\bversionCode=" + str(release['version_code']) + r"\b", actual):
        raise Error("La versión instalada no coincide con la distribución")
    me = "tv.lightos"
    steps = [
        ("appops", "set", me, "ACCESS_RESTRICTED_SETTINGS", "allow"),
        ("pm", "grant", me, "android.permission.READ_TV_LISTINGS"),
        ("appops", "set", me, "GET_USAGE_STATS", "allow"),
        ("cmd", "notification", "allow_listener", f"{me}/{me}.MediaWatcher"),
        ("pm", "grant", me, "android.permission.WRITE_SECURE_SETTINGS"),
        ("appops", "set", me, "WRITE_SETTINGS", "allow"),
    ]
    skipped = []
    for step in steps:
        try:
            a.shell(*step)
        except Error:
            skipped.append(" ".join(step[:2]))
    current = a.optional("settings", "get", "secure", "enabled_accessibility_services").get("value", "")
    services = [x for x in current.split(":") if x and x != "null"]
    if f"{me}/{me}.HorizonService" not in services:
        services.append(f"{me}/{me}.HorizonService")
    a.shell("settings", "put", "secure", "enabled_accessibility_services", ":".join(services))
    a.shell("settings", "put", "secure", "accessibility_enabled", "1")
    print("Instalación verificada. Se conservaron los datos existentes.")
    if skipped:
        print("Permisos opcionales no disponibles: " + ", ".join(skipped))
    make_home(a)
    a.shell("am", "start", "-n", "tv.lightos/.MainActivity")


NOT_LAUNCHERS = {"com.android.tv.settings", "com.android.settings", "com.android.provision",
                 "com.google.android.tungsten.setupwraith", "com.android.managedprovisioning"}
KNOWN_LAUNCHERS = ["com.google.android.apps.tv.launcherx", "com.google.android.tvlauncher", "com.google.android.leanbacklauncher"]
HOME_RECORD = STATE / "inicio.json"


def current_home(a: Adb) -> str:
    out = a.optional("cmd", "package", "resolve-activity", "--brief", "-c", "android.intent.category.HOME",
                     "-a", "android.intent.action.MAIN").get("value", "").strip().splitlines()
    return out[-1].strip() if out else ""


def home_packages(a: Adb) -> list[str]:
    """Packages Android lists as Home, any brand; HorizonX and settings fall-backs left out."""
    raw = a.optional("cmd", "package", "query-activities", "--brief", "--user", "0",
                     "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME").get("value", "")
    found = [l.strip().split("/")[0] for l in raw.splitlines() if "/" in l and " " not in l.strip()]
    found = [p for p in dict.fromkeys(found) if p != "tv.lightos" and p not in NOT_LAUNCHERS]
    return [p for p in KNOWN_LAUNCHERS if p in found] + [p for p in found if p not in KNOWN_LAUNCHERS]


def make_home(a: Adb) -> None:
    """Use the audited Home transaction; never overwrite an already-active Home backup."""
    from . import home
    from .store import Store
    from .transactions import token
    if current_home(a).startswith("tv.lightos/"):
        print("HorizonX ya es el inicio. Se conserva el respaldo anterior.")
        return
    sdk = int(a.shell("getprop", "ro.build.version.sdk").strip())
    if sdk < 29:
        print("Elige HorizonX en Ajustes → Aplicaciones predeterminadas → Inicio. No se apartó ningún paquete.")
        return
    store = Store(STATE / "home")
    try:
        plan = home.prepare(a, store)
    except Error as error:
        print("Instalación correcta; activación automática no disponible: " + str(error))
        return
    print("Inicio anterior: " + plan['before_home'])
    print("Respaldo del plan: " + str(store.path(plan['id'])))
    if yes("¿Activar HorizonX como inicio con este respaldo y comprobación de Home?"):
        result = home.activate(a, store, plan['id'], token('ACTIVAR-INICIO', plan))
        print("Resultado Home: " + result['status'])


def restore_home(a: Adb) -> None:
    from . import home
    from .device import identity, binding
    from .store import Store
    from .transactions import token
    store = Store(STATE / "home")
    device = identity(a)
    records = [store.load(name) for name in store.records('home-transaction-')]
    matching = [r for r in records if binding(r.get('device', {})) == binding(device) and r.get('status') not in ('restored', 'rolled-back')]
    if not matching:
        print("No hay un respaldo Home autenticado para esta TV en este PC. Usa HorizonX → Ajustes → Sistema → Volver al inicio original. No se habilitó ningún paquete por suposición.")
        return
    record = max(matching, key=lambda r: r.get('created', ''))
    print("Inicio a restaurar: " + record['before_home'])
    if yes("¿Restaurar este inicio y sus estados anteriores?"):
        result = home.restore(a, store, record['id'], token('RESTAURAR-INICIO', record))
        print("Resultado de restauración: " + result['status'])


def optimise(a: Adb) -> None:
    dev = optimize.device_info(a)
    describe(dev)
    plan = optimize.plan(dev, "recomendado")
    if not plan["actions"]:
        print("No hay cambios de optimización verificados para proponer. Esto no demuestra que la TV esté optimizada.")
        return
    print(f"\nSe deshabilitarán {len(plan['actions'])} componentes (no se borra nada, se puede deshacer):")
    for x in plan["actions"]:
        print(f"  - {x['name']:<48} {x['reason'][:60]}")
    if plan["offered"]:
        print("\nNo se tocan (los usas o son opcionales): " + ", ".join(o["name"] for o in plan["offered"][:10]))
    if yes("\n¿Aplicar ahora?"):
        backup = optimize.apply(a, dev, plan, STATE)
        print(f"Hecho. Copia para deshacer: {backup}\nReinicia el televisor para liberar memoria.")


def restore(a: Adb) -> None:
    backups = sorted(STATE.glob("optimizacion-*.json"))
    if not backups:
        print("No hay optimizaciones guardadas en este PC.")
        return
    for b in backups:
        rec = json.loads(b.read_text(encoding="utf-8"))
        print(f"{b.name}: {len(rec.get('before', {}))} componentes" + (" (ya restaurada)" if rec.get("restored") else ""))
    if yes("¿Reactivar todo lo deshabilitado?"):
        for b in backups:
            optimize.restore(a, b)
        print("Restaurado.")


def compatibility() -> None:
    for p in optimize.platforms()["platforms"]:
        mark = "✓" if p["apk"] else "✗"
        print(f"\n{mark} {p['name']}\n   {p['notes']}")


def main() -> int:
    print("HorizonX · asistente para el televisor\n")
    try:
        adb = adb_path()
    except Error as e:
        print(e)
        compatibility()
        return 1
    tv: Adb | None = None
    while True:
        print("\n1. Conectar televisor\n2. Instalar HorizonX\n3. Revisar optimización opcional\n"
              "4. Deshacer optimización\n5. Volver al inicio original\n6. ¿Es compatible mi televisor?\n0. Salir")
        choice = ask("Opción: ")
        try:
            if choice == "0":
                return 0
            if choice == "6":
                compatibility()
                continue
            if choice in "12345" and choice and (tv is None or choice == "1"):
                tv = connect(adb)
                if tv is None:
                    print("No se pudo conectar.")
                    continue
                if choice == "1":
                    describe(optimize.device_info(tv))
                    continue
            {"2": install, "3": optimise, "4": restore}.get(choice, lambda t: None)(tv)
            if choice == "5":
                restore_home(tv)
        except Error as e:
            print(f"Error: {e}")
