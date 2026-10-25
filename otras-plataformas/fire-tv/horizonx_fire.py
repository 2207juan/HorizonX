#!/usr/bin/env python3
"""HorizonX for Amazon Fire TV (Fire OS 7/8): guided installer and reversible clean-up over ADB.

  python3 horizonx_fire.py                 menu
  python3 horizonx_fire.py status  --tv IP
  python3 horizonx_fire.py install --tv IP
  python3 horizonx_fire.py clean   --tv IP   (asks before changing anything; keeps a backup)
  python3 horizonx_fire.py restore --tv IP

The same HorizonX APK as Android TV is used. Amazon's launcher is never disabled: HorizonX opens on
top of it when Home is pressed (accessibility redirect, Fire OS only). Vega OS devices are detected
and sent to the Vega instructions, because they cannot run APKs.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# The ADB helper ships next to this file in the download; in the source tree it lives in companion/.
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(HERE))
from horizonx.adb import Adb, Error  # noqa: E402

PKG = "tv.lightos"
DEVICES = json.loads((HERE.parent / "data" / "devices.json").read_text(encoding="utf-8"))
DEBLOAT = json.loads((HERE.parent / "data" / "debloat.json").read_text(encoding="utf-8"))
STATE = Path.home() / ".horizonx" / "fire"


def say(t=""):
    print(t, flush=True)


def ask(t):
    try:
        return input(t).strip()
    except EOFError:
        return ""


def yes(t):
    return ask(f"{t} [s/N]: ").lower() in ("s", "si", "sí", "y", "yes")


def adb_path():
    found = shutil.which("adb")
    if not found:
        sys.exit("No encuentro ADB. Instala «Android SDK Platform-Tools» y vuelve a abrir el asistente.")
    return found


def connect(ip):
    adb = adb_path()
    if not ip:
        say("En el Fire TV: Ajustes → Mi Fire TV → Acerca de → pulsa 7 veces el nombre del dispositivo.")
        say("Después: Mi Fire TV → Opciones de desarrollador → Depuración ADB: activada.")
        say("La IP está en Mi Fire TV → Acerca de → Red.")
        ip = ask("IP del Fire TV: ")
        if not ip:
            sys.exit(1)
    target = ip if ":" in ip else f"{ip}:5555"
    try:
        subprocess.run([adb, "connect", target], capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        sys.exit(f"El Fire TV no responde en {target}. ¿Está encendido, en la misma red y con la depuración ADB activada?")
    for _ in range(30):
        out = subprocess.run([adb, "devices"], capture_output=True, text=True).stdout
        line = next((l for l in out.splitlines() if l.startswith(target)), "")
        if line.endswith("device"):
            return Adb(target, adb)
        if line.endswith("unauthorized"):
            say("En la pantalla del Fire TV acepta «¿Permitir depuración?» (marca «Permitir siempre»)…")
        time.sleep(2)
    sys.exit("No se pudo conectar. Comprueba la IP y que la depuración ADB esté activada.")


def describe(a: Adb):
    prop = lambda k: a.optional("getprop", k).get("value", "")  # noqa: E731
    model, sdk = prop("ro.product.model"), int(prop("ro.build.version.sdk") or 0)
    fire = "amazon.hardware.fire_tv" in a.optional("pm", "list", "features").get("value", "")
    version = prop("ro.build.version.name") or prop("ro.build.display.id")
    row = next((d for d in DEVICES["devices"] if d["model_code"] == model), None)
    return {"model": model, "sdk": sdk, "fire": fire, "version": version, "row": row}


def cmd_status(args, a=None):
    a = a or connect(args.tv)
    d = describe(a)
    say(f"\nModelo: {d['row']['name'] if d['row'] else d['model']} ({d['model']})  ·  {d['version']}  ·  Android API {d['sdk']}")
    if not d["fire"]:
        say("No es un Fire TV. Para Android TV / Google TV usa el asistente principal de HorizonX.")
    elif d["sdk"] < 26:
        say("No compatible: HorizonX necesita Fire OS 7 u 8 (Android 9 o superior).")
    else:
        say("Compatible (según documentación): HorizonX + apertura con Home sobre el inicio de Amazon.")
        if d["sdk"] < 30:
            say("Fire OS 7: el sistema retrasa hasta ~5 s las apps abiertas con Home. En Fire OS 8 es inmediato.")
    say("HorizonX aún no se ha probado físicamente en ningún Fire TV.")
    return d


def latest_apk():
    found = sorted(HERE.glob("HorizonX-*.apk")) + sorted((ROOT / "dist").glob("HorizonX-[0-9]*.apk"))
    if not found:
        sys.exit("No encuentro HorizonX-x.y.z.apk junto al asistente.")
    return found[-1]


def cmd_install(args):
    a = connect(args.tv)
    d = cmd_status(args, a)
    if not d["fire"] or d["sdk"] < 26:
        return
    apk = latest_apk()
    say(f"\nInstalando {apk.name}…")
    say(a.command("install", "-r", str(apk), timeout=240))
    for step in (("pm", "grant", PKG, "android.permission.WRITE_SECURE_SETTINGS"),
                 ("pm", "grant", PKG, "android.permission.READ_TV_LISTINGS"),
                 ("appops", "set", PKG, "GET_USAGE_STATS", "allow"),
                 ("cmd", "notification", "allow_listener", f"{PKG}/{PKG}.MediaWatcher")):
        a.optional(*step)
    service = f"{PKG}/{PKG}.HorizonService"
    current = a.optional("settings", "get", "secure", "enabled_accessibility_services").get("value", "")
    services = [s for s in current.split(":") if s and s != "null"]
    if service not in services:
        services.append(service)
    a.shell("settings", "put", "secure", "enabled_accessibility_services", ":".join(services))
    a.shell("settings", "put", "secure", "accessibility_enabled", "1")
    a.optional("monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    say("✓ HorizonX instalado. Pulsa Home: se abrirá sobre el inicio de Amazon.")
    say("  Para ir al inicio de Amazon: HorizonX → Ajustes → Sistema → «Ir al inicio de Amazon».")


def enabled_packages(a):
    out = a.shell("pm", "list", "packages", "-e")
    return {l.split(":", 1)[1].strip() for l in out.splitlines() if l.startswith("package:")}


def cmd_clean(args):
    a = connect(args.tv)
    d = cmd_status(args, a)
    if not d["fire"]:
        return
    present = enabled_packages(a)
    safe = [e for e in DEBLOAT["safe"] if e["name"] in present]
    optional = [e for e in DEBLOAT["optional"] if e["name"] in present]
    if not safe and not optional:
        say("No queda nada que limpiar.")
        return
    say("\nSe desactivarán (sin borrar, reversible):")
    for e in safe:
        say(f"  ✓ {e['why']:<44} {e['name']}")
    chosen = list(safe)
    if optional:
        say("\nOpcionales (solo si no los usas):")
        for i, e in enumerate(optional, 1):
            say(f"  {i:>2}. {e['why']:<40} {e['name']}")
        pick = ask("Números de los opcionales a desactivar (ej. 1 3 5), o Enter para ninguno: ")
        chosen += [optional[int(n) - 1] for n in pick.replace(",", " ").split() if n.isdigit() and 0 < int(n) <= len(optional)]
    if not yes(f"\n¿Desactivar {len(chosen)} componentes?"):
        return
    STATE.mkdir(parents=True, exist_ok=True)
    backup = STATE / f"limpieza-{d['model']}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    record = {"model": d["model"], "version": d["version"], "disabled": []}
    for e in chosen:
        if e["name"] in DEBLOAT["never"]:
            continue
        out = a.optional("pm", "disable-user", "--user", "0", e["name"])
        if "disabled" in out.get("value", ""):
            record["disabled"].append(e["name"])
            say(f"  ✓ {e['name']}")
        backup.write_text(json.dumps(record, indent=1), encoding="utf-8")
    say(f"\nHecho. Copia para deshacer: {backup}\nReinicia el Fire TV para liberar memoria.")


def cmd_restore(args):
    a = connect(args.tv)
    files = sorted(STATE.glob("limpieza-*.json"))
    if not files:
        say("No hay limpiezas guardadas en este PC.")
        return
    for f in files:
        for name in json.loads(f.read_text(encoding="utf-8")).get("disabled", []):
            a.optional("pm", "enable", "--user", "0", name)
            say(f"  ↺ {name}")
        f.rename(f.with_suffix(".restored"))
    say("Restaurado.")


def menu():
    say("HorizonX · Amazon Fire TV\n")
    actions = {"1": ("¿Es compatible mi Fire TV?", cmd_status), "2": ("Instalar HorizonX", cmd_install),
               "3": ("Limpiar publicidad y telemetría", cmd_clean), "4": ("Deshacer la limpieza", cmd_restore)}
    while True:
        for k, (label, _) in actions.items():
            say(f"{k}. {label}")
        say("0. Salir")
        c = ask("Opción: ")
        if c in ("0", ""):
            return
        if c in actions:
            try:
                actions[c][1](argparse.Namespace(tv=None))
            except (Error, SystemExit) as e:
                say(f"{e}")
            say("")


def main():
    p = argparse.ArgumentParser(description="HorizonX para Amazon Fire TV")
    p.add_argument("command", nargs="?", choices=["status", "install", "clean", "restore"])
    p.add_argument("--tv")
    args = p.parse_args()
    if not args.command:
        menu()
        return
    {"status": cmd_status, "install": cmd_install, "clean": cmd_clean, "restore": cmd_restore}[args.command](args)


if __name__ == "__main__":
    main()
