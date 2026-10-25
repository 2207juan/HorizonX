"""Guided menu for people who never used ADB: connect, install, optimise, restore.

Opened by double-clicking HorizonX.sh / HorizonX.cmd with no arguments. Every change asks first.
"""
from __future__ import annotations

import json
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
          "Sin perfil exacto: se usarán solo componentes comprobados en muchos modelos.")


def install(a: Adb) -> None:
    apk = sorted(HERE.glob("HorizonX-*.apk")) or sorted((HERE.parent / "dist").glob("HorizonX-*.apk"))
    if not apk:
        print("No encuentro el archivo HorizonX-x.y.z.apk junto a este asistente.")
        return
    print(f"Instalando {apk[-1].name}...")
    print(a.command("install", "-r", str(apk[-1]), timeout=180))
    me = "tv.lightos"
    steps = [
        ("appops", "set", me, "ACCESS_RESTRICTED_SETTINGS", "allow"),
        ("pm", "grant", me, "android.permission.READ_TV_LISTINGS"),
        ("appops", "set", me, "GET_USAGE_STATS", "allow"),
        ("cmd", "notification", "allow_listener", f"{me}/{me}.MediaWatcher"),
        ("pm", "grant", me, "android.permission.WRITE_SECURE_SETTINGS"),
        ("appops", "set", me, "WRITE_SETTINGS", "allow"),
    ]
    for s in steps:
        try:
            a.shell(*s)
        except Error:
            pass
    current = a.optional("settings", "get", "secure", "enabled_accessibility_services").get("value", "")
    services = [x for x in current.split(":") if x and x != "null"]
    if f"{me}/{me}.HorizonService" not in services:
        services.append(f"{me}/{me}.HorizonService")
    a.shell("settings", "put", "secure", "enabled_accessibility_services", ":".join(services))
    a.shell("settings", "put", "secure", "accessibility_enabled", "1")
    print("HorizonX instalado con sus permisos (volumen, Continuar viendo y autoreparación).")
    if yes("¿Usar HorizonX como pantalla de inicio del televisor?"):
        make_home(a)


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
    """Select HorizonX; only if the TV keeps its own launcher in front, set launchers aside one by one."""
    before = current_home(a)
    print(a.shell("cmd", "package", "set-home-activity", "--user", "0", "tv.lightos/.MainActivity"))
    aside: list[str] = []
    if not current_home(a).startswith("tv.lightos/"):
        for pkg in home_packages(a):
            a.shell("pm", "disable-user", "--user", "0", pkg)
            aside.append(pkg)
            print(f"  Inicio original apartado (reversible): {pkg}")
            if current_home(a).startswith("tv.lightos/"):
                break
    STATE.mkdir(parents=True, exist_ok=True)
    HOME_RECORD.write_text(json.dumps({"before": before, "aside": aside}), encoding="utf-8")
    print("HorizonX es la pantalla de inicio." if current_home(a).startswith("tv.lightos/")
          else "El televisor no aceptó otro inicio. HorizonX se abrirá encima del inicio del televisor.")


def restore_home(a: Adb) -> None:
    """Put back exactly what make_home set aside (older installs: Google TV)."""
    try:
        record = json.loads(HOME_RECORD.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        record = {"before": "com.google.android.apps.tv.launcherx",
                  "aside": ["com.google.android.apps.tv.launcherx", "com.google.android.tungsten.setupwraith"]}
    for pkg in record.get("aside", []):
        a.optional("pm", "enable", "--user", "0", pkg)
    target = record.get("before", "")
    if not target or target.startswith("tv.lightos/"):
        target = next(iter(home_packages(a)), "")
    if target:
        a.optional("cmd", "package", "set-home-activity", "--user", "0", target)
    HOME_RECORD.unlink(missing_ok=True)
    print("Inicio original reactivado.")


def optimise(a: Adb) -> None:
    dev = optimize.device_info(a)
    describe(dev)
    plan = optimize.plan(dev, "recomendado")
    if not plan["actions"]:
        print("Este televisor ya está optimizado.")
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
        print("\n1. Conectar televisor\n2. Instalar HorizonX\n3. Optimizar (quitar publicidad y procesos)\n"
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
