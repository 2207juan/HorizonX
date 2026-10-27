#!/usr/bin/env python3
"""HorizonX for Amazon Fire TV (Fire OS 7/8): guided installer and reversible clean-up over ADB.

  python3 horizonx_fire.py                 menu
  python3 horizonx_fire.py status  --tv IP
  python3 horizonx_fire.py install --tv IP
  python3 horizonx_fire.py clean   --tv IP   (asks before changing anything; keeps a backup)
  python3 horizonx_fire.py restore --tv IP

The Fire-specific APK shares the Android UI. Amazon's launcher is never disabled: HorizonX opens on
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
import home_transaction

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
        say("Candidato por sistema: APK + redirección experimental de Home. No es compatibilidad física verificada.")
        if d["sdk"] < 30:
            say("Fire OS 7: otros proyectos documentan retrasos de hasta ~5 s al abrir apps desde Home.")
    say("HorizonX aún no se ha probado físicamente en ningún Fire TV.")
    return d


def latest_apk():
    fire = list(HERE.glob('HorizonX-FireOS-*.apk')) + list((ROOT / 'dist').glob('HorizonX-FireOS-*.apk'))
    found = fire
    if not found:
        sys.exit("No encuentro HorizonX-FireOS-*.apk. Compila la edición Fire OS; la APK Android normal no incluye esta política de arranque.")
    import re
    return max(found, key=lambda f: tuple(map(int, re.findall(r'\d+', f.stem))))


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
    a.optional("monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    say("✓ APK instalada. Esto NO demuestra arranque automático ni redirección de Home.")
    say("  Activación separada y reversible: home-plan → home-activate con el token del plan.")


def enabled_packages(a):
    out = a.shell("pm", "list", "packages", "-e")
    return {l.split(":", 1)[1].strip() for l in out.splitlines() if l.startswith("package:")}


def cmd_clean(args):
    a = connect(args.tv)
    d = cmd_status(args, a)
    if not d["fire"]:
        return
    ident = home_transaction.identity(a)
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
    record = {"model": d["model"], "version": d["version"], "identity": ident, "disabled": [], "pending": []}
    home_transaction.write(backup, record, exclusive=True)
    for e in chosen:
        if e["name"] in DEBLOAT["never"]:
            continue
        record["pending"] = [e["name"]]
        home_transaction.write(backup, record)
        out = a.optional("pm", "disable-user", "--user", "0", e["name"])
        if "disabled" in out.get("value", ""):
            record["disabled"].append(e["name"])
            say(f"  ✓ {e['name']}")
            record["pending"] = []
        else:
            # A lost reply may have applied the change. Keep it recoverable and stop.
            home_transaction.write(backup, record)
            raise home_transaction.HomeError("Respuesta de desactivación ambigua; restaura/revisa " + str(backup))
        home_transaction.write(backup, record)
    say(f"\nHecho. Copia para deshacer: {backup}\nReinicia el Fire TV para liberar memoria.")


def cmd_restore(args):
    a = connect(args.tv)
    ident = home_transaction.identity(a)
    files = sorted(STATE.glob("limpieza-*.json"))
    if not files:
        say("No hay limpiezas guardadas en este PC.")
        return
    for f in files:
        record = json.loads(f.read_text(encoding="utf-8"))
        if record.get("identity") != ident:
            say(f"Omitido {f.name}: otra TV/firmware o respaldo antiguo sin identidad; requiere revisión.")
            continue
        restore_cleanup(a, f, ident)


def restore_cleanup(a, path, ident):
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("identity") != ident:
        raise home_transaction.HomeError("Respaldo de limpieza de otra TV/firmware o sin identidad")
    import re
    names = record.get("disabled", []) + record.get("pending", [])
    if any(not isinstance(n, str) or not re.fullmatch(r'[A-Za-z0-9_.]+', n) for n in names):
        raise home_transaction.HomeError("Lista de restauración no válida")
    for name in dict.fromkeys(names):
        a.shell("pm", "enable", "--user", "0", name)
        if name not in enabled_packages(a):
            raise home_transaction.HomeError("No se pudo verificar la restauración de " + name)
        say(f"  ↺ {name}")
    path.rename(path.with_suffix(".restored"))
    say("Restauración verificada: " + path.name)


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
            except (Error, home_transaction.HomeError, OSError, ValueError, SystemExit) as e:
                say(f"{e}")
            say("")


def main():
    p = argparse.ArgumentParser(description="HorizonX para Amazon Fire TV")
    p.add_argument("command", nargs="?", choices=["status", "install", "clean", "restore", "home-plan", "home-activate", "home-restore"])
    p.add_argument("--tv")
    p.add_argument("--backup", type=Path, help="Archivo nuevo para el plan de Home")
    p.add_argument("--approve", help="Token del plan: consentimiento explícito para activación/restauración")
    args = p.parse_args()
    if not args.command:
        menu()
        return
    if args.command.startswith('home-'):
        if not args.backup:
            p.error('--backup FILE requerido')
        try:
            a = connect(args.tv)
            if args.command == 'home-plan':
                token = home_transaction.plan(a, args.backup)
                say('Plan de solo lectura guardado. Token: ' + token)
            elif args.command == 'home-activate':
                home_transaction.activate(a, args.backup, args.approve)
                say('Accesibilidad configurada. Home y arranque aún requieren pruebas físicas; no se declara éxito por estos ajustes.')
            else:
                home_transaction.restore(a, args.backup, args.approve)
                say('Cambio de accesibilidad restaurado. Comprueba Home con el mando físico.')
        except (home_transaction.HomeError, Error, OSError, ValueError) as e:
            p.exit(2, str(e) + '\n')
    else:
        try:
            {"status": cmd_status, "install": cmd_install, "clean": cmd_clean, "restore": cmd_restore}[args.command](args)
        except (home_transaction.HomeError, Error, OSError, ValueError) as e:
            p.exit(2, str(e) + '\n')


if __name__ == "__main__":
    main()
