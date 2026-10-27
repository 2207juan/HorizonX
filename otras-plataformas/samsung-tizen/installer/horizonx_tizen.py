#!/usr/bin/env python3
"""HorizonX for Samsung Tizen: guided installer for people who never used a developer tool.

Double-click HorizonX-Samsung.sh / .cmd, or run with a command:
  python3 horizonx_tizen.py                  menu
  python3 horizonx_tizen.py status [--tv IP] what the TV is and what HorizonX can do on it
  python3 horizonx_tizen.py install [--tv IP] [--no-optimize]
  python3 horizonx_tizen.py apps [--tv IP]   installed apps, with suggestions
  python3 horizonx_tizen.py uninstall [--tv IP]

Uses the TV's developer connection (SDB, port 26101) and local API (port 8001). It never roots
the TV, changes firmware or touches Samsung system packages (org.tizen.*, com.samsung.*).
SDB, certificates and package signing come from AeroTizen (MIT), vendored unmodified.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from third_party.aerotizen import catalog, discover  # noqa: E402
from third_party.aerotizen.sdb import Sdb, SdbError  # noqa: E402

APP_ID = "HrznXTV001.HorizonX"
PKG_ID = APP_ID.split(".")[0]
STATE = Path.home() / ".horizonx" / "tizen"
DB = json.loads((HERE.parent / "data" / "devices.json").read_text(encoding="utf-8"))
catalog.PROTECTED_PKGS.add(PKG_ID)
# Removed automatically after installing: never a streaming or music service someone may use,
# only manuals, shop demos, tips and fitness extras. Each one comes back from Samsung Apps.
AUTO_REMOVE_HINTS = ("e-manual", "emanual", "user guide", "demo", "retail", "store mode", "tips",
                     "samsung health", "workout", "fitness")
# What no app or SDB command can change on a Samsung TV: printed once, never shown inside HorizonX.
TV_SETTINGS = [
    "Ajustes → General y privacidad → Opciones de pantalla de inicio → «Iniciar con Smart Hub Inicio»: desactivado",
    "… → «Reproducción automática de Samsung TV Plus»: desactivado",
    "Ajustes → General y privacidad → Términos y privacidad → Servicios de información de visualización: desactivado",
    "… → Publicidad basada en intereses: desactivado",
]


def say(text=""):
    print(text, flush=True)


def ask(text):
    try:
        return input(text).strip()
    except EOFError:
        return ""


def yes(text):
    return ask(f"{text} [s/N]: ").lower() in ("s", "si", "sí", "y", "yes")


def tv_info(ip):
    """Read /api/v2/ (works with Developer Mode off). None if the TV does not answer."""
    try:
        return json.load(urllib.request.urlopen(f"http://{ip}:8001/api/v2/", timeout=4))["device"]
    except Exception:
        return None


def model_year(device):
    """Year from the internal model name (e.g. 21_KANTSU2E...), else from the retail code letter."""
    m = re.match(r"(\d{2})_", device.get("model") or "")
    if m:
        return 2000 + int(m.group(1))
    code = device.get("modelName") or ""
    letters = {y["letter"]: y["year"] for y in DB["years"] if y.get("letter")}
    # Retail codes: prefix + size, then either YEAR+"U"+digits (Crystal/LED: UN65DU7200, UE55KU6000)
    # or series + YEAR (QLED/OLED/Frame: QE75Q60B, QN65QN90F, QE65S90C, QE65LS03D, UN65U8000F).
    m = re.match(r"^[A-Z]{2}\d{2}(.*)$", code)
    if not m:
        return None
    rest = m.group(1)
    m = re.match(r"^([A-Z])U\d", rest) or re.match(r"^[A-Z]*\d+([A-Z])", rest)
    return letters.get(m.group(1)) if m else None


def compatibility(device):
    year = model_year(device)
    row = next((y for y in DB["years"] if y["year"] == year), None)
    tizen = device.get("OS") or ""
    lines = [f"Modelo: {device.get('modelName')}  ({device.get('model')})",
             f"Año: {year or 'desconocido'}  ·  Sistema: {tizen or (row and 'Tizen ' + row['tizen']) or '?'}",
             f"Modo desarrollador: {'activado' if str(device.get('developerMode')) == '1' else 'desactivado'}"
             + (f" (PC autorizado: {device.get('developerIP')})" if str(device.get('developerMode')) == '1' else "")]
    if not year:
        lines.append("No reconozco el año: HorizonX debería funcionar en cualquier Samsung Tizen de 2017 en adelante.")
    elif year < 2017:
        lines.append("2015–2016: HorizonX se puede instalar, pero no abrirse sola al encender (sin servicio de arranque garantizado).")
    else:
        lines.append("Compatible (según documentación): app + vuelta automática con Home.")
    if row and row.get("third_party"):
        lines.append("Probado por otros proyectos en: " + "; ".join(row["third_party"]))
    lines.append("HorizonX aún no se ha probado físicamente en ningún Samsung (estado: documentado).")
    return lines


def pick_tv(ip=None):
    if ip:
        if tv_info(ip):
            return ip
        sys.exit(f"No encuentro un Samsung en {ip}. ¿Está encendido y en la misma red?")
    say("Buscando televisores Samsung en tu red…")
    tvs = discover.discover()
    if not tvs:
        ip = ask("No encontré ninguno automáticamente. Escribe la IP del televisor (Ajustes → General → Red → Estado de red): ")
        return pick_tv(ip) if ip else sys.exit(1)
    if len(tvs) == 1:
        say(f"Encontrado: {tvs[0]['name']} ({tvs[0]['ip']})")
        return tvs[0]["ip"]
    for i, t in enumerate(tvs, 1):
        say(f"  {i}. {t['name']}  {t['ip']}  {t.get('model') or ''}")
    n = ask("Número del televisor: ")
    return tvs[int(n) - 1]["ip"] if n.isdigit() and 0 < int(n) <= len(tvs) else sys.exit(1)


def developer_mode_help(ip):
    say("\nHay que activar el modo desarrollador una vez:")
    say("  1. En el televisor abre «Apps».")
    say("  2. Escribe 1 2 3 4 5 con el mando (o con el teclado numérico en pantalla).")
    say("  3. Activa «Developer mode» y escribe la IP de este PC: " + local_ip(ip))
    say("  4. Desenchufa el televisor de la corriente 1 minuto (apagarlo con el mando no basta).")
    say("  5. Vuelve a ejecutar este asistente.")


def local_ip(tv_ip):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((tv_ip, 9))
        return s.getsockname()[0]
    except OSError:
        return "?"
    finally:
        s.close()


def sdb(ip):
    s = Sdb(ip)
    try:
        s.connect()
    except SdbError as e:
        developer_mode_help(ip)
        sys.exit(f"\nNo se pudo abrir la conexión de desarrollador: {e}")
    return s


def need_crypto():
    try:
        import cryptography  # noqa: F401
    except ImportError:
        sys.exit("Falta la librería «cryptography» para firmar. Instálala con:\n  python3 -m pip install --user cryptography")


def build_package():
    """Use the unsigned .wgt from the release, or build it from source when present."""
    dist = sorted((HERE.parent.parent.parent / "dist").glob("HorizonX-Tizen-*-unsigned.wgt")) + sorted(HERE.glob("HorizonX-Tizen-*-unsigned.wgt"))
    if dist:
        return dist[-1]
    builder = HERE.parent / "tools" / "build_wgt.py"
    if builder.exists():
        os.system(f'"{sys.executable}" "{builder}"')
        return build_package()
    sys.exit("No encuentro HorizonX-Tizen-…-unsigned.wgt junto al asistente.")


def cmd_status(args):
    ip = pick_tv(args.tv)
    for line in compatibility(tv_info(ip)):
        say(line)


def cmd_install(args):
    need_crypto()
    from third_party.aerotizen import certs, signer
    ip = pick_tv(args.tv)
    device = tv_info(ip)
    for line in compatibility(device):
        say(line)
    if str(device.get("developerMode")) != "1":
        developer_mode_help(ip)
        return
    package = build_package()
    with zipfile.ZipFile(package) as z:
        version = re.search(rb'version="([^"]+)"', z.read("config.xml")).group(1).decode()
    with sdb(ip) as s:
        duid = s.duid()
        tool_path = s.capability().get("sdk_toolpath", "/home/owner/share/tmp/sdk_tools")
        cert_dir = STATE / "certs" / duid
        if not (cert_dir / "distributor.p12").exists():
            say("\nSamsung solo deja instalar apps firmadas con un certificado de tu cuenta Samsung para este televisor.")
            say("Se abrirá el navegador para que inicies sesión. HorizonX no ve tu contraseña: Samsung entrega un permiso temporal.")
            if not yes("¿Abrir el inicio de sesión de Samsung ahora?"):
                return
            certs.create_profile(duid, str(cert_dir))
            say(f"Certificados guardados en {cert_dir}")
        signed = STATE / f"{PKG_ID}-signed.wgt"
        signed.parent.mkdir(parents=True, exist_ok=True)
        signer.sign_wgt(str(package), str(signed), str(cert_dir))
        s.push((cert_dir / "device-profile.xml").read_bytes(), f"{tool_path}/device-profile.xml")
        say(f"Instalando HorizonX {version}…")
        output = s.install(APP_ID, signed.read_bytes(), tool_path)
        installed = next((a for a in catalog.parse_applist(s.applist()) if a.get("appid") == APP_ID), None)
        if not installed or re.search(r"\b(fail(ed|ure)?|error|denied)\b", output, re.I):
            say(output.strip()[-600:])
            sys.exit("El televisor no confirmó la instalación.")
        say(f"✓ HorizonX instalado (versión {installed.get('version') or version}).")
        if getattr(args, "optimize", False) and not getattr(args, "no_optimize", False) and yes("¿Autorizar quitar los extras opcionales? Guarda antes tus datos; no es necesario para activar Home."):
            optimize(s, duid)
        if yes("¿Abrirlo ahora?"):
            s.launch(APP_ID)
    say("\nLa app está instalada. Arranque y Home siguen siendo experimentales: pruébalos por separado desde apps externas.")
    say("El vigilante se configura en HorizonX → Ajustes → Sistema; no equivale a reasignar el Home nativo.")
    say("\nSamsung no deja que ninguna app cambie estos ajustes; si quieres menos publicidad, hazlo una vez en el televisor:")
    for line in TV_SETTINGS:
        say(f"  · {line}")


def optimize(s, duid):
    """Optional authorized clean-up: removes the listed extras and records them."""
    apps = catalog.parse_applist(s.applist())
    targets = [a for a in apps if catalog.classify(a) == "bloat"
               and any(h in (a.get("name") or "").lower() for h in AUTO_REMOVE_HINTS)]
    if not targets:
        say("✓ Optimización: no hay extras que quitar en este televisor.")
        return
    record = STATE / f"optimizacion-{duid}.json"
    removed = json.loads(record.read_text(encoding="utf-8")) if record.exists() else []
    for a in targets:
        pkg = a.get("pkgid") or a.get("appid", "").split(".")[0]
        out = s.uninstall(pkg)
        ok = not re.search(r"\b(fail(ed|ure)?|error|denied|not ?allowed)\b", out, re.I)
        say(f"  {'✓ quitada' if ok else '· no se pudo quitar'}: {a.get('name') or pkg}")
        if ok:
            removed.append({"name": a.get("name"), "pkgid": pkg})
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps(removed, ensure_ascii=False, indent=1), encoding="utf-8")
    say(f"Lista guardada en {record}. Se pueden volver a instalar desde Samsung Apps.")


def cmd_apps(args):
    ip = pick_tv(args.tv)
    with sdb(ip) as s:
        apps = catalog.parse_applist(s.applist())
    rows = [(catalog.classify(a), a) for a in apps]
    for label, title in (("bloat", "Probablemente no las usas"), ("optional", "Opcionales"), ("protected", "Del sistema (no se tocan)")):
        group = [a for c, a in rows if c == label]
        if group:
            say(f"\n{title} ({len(group)}):")
            for a in sorted(group, key=lambda x: (x.get("name") or "").lower())[:60]:
                say(f"  {a.get('name') or '?':<36} {a.get('pkgid') or a.get('appid')}")
    say("\nPara borrar apps en Tizen 6 o posterior: Apps → Ajustes (engranaje) → elige la app → Eliminar.")


def cmd_uninstall(args):
    ip = pick_tv(args.tv)
    if not yes("¿Quitar HorizonX de este televisor? El inicio de Samsung vuelve a ser el normal."):
        return
    with sdb(ip) as s:
        say(s.uninstall(PKG_ID).strip()[-300:])


def menu():
    say("HorizonX · Samsung Tizen\n")
    actions = {"1": ("¿Es compatible mi televisor?", cmd_status), "2": ("Instalar o actualizar HorizonX", cmd_install),
               "3": ("Ver apps instaladas y sugerencias", cmd_apps), "4": ("Quitar HorizonX", cmd_uninstall)}
    while True:
        for k, (label, _) in actions.items():
            say(f"{k}. {label}")
        say("0. Salir")
        choice = ask("Opción: ")
        if choice == "0" or not choice:
            return
        if choice in actions:
            try:
                actions[choice][1](argparse.Namespace(tv=None, no_optimize=True, optimize=False))
            except SystemExit as e:
                if e.code not in (None, 0):
                    say(str(e.code))
            say("")


def main():
    p = argparse.ArgumentParser(description="HorizonX para Samsung Tizen")
    p.add_argument("command", nargs="?", choices=["status", "install", "apps", "uninstall"])
    p.add_argument("--tv", help="IP del televisor")
    p.add_argument("--no-optimize", action="store_true", help="no quitar manuales, demos ni extras al instalar")
    p.add_argument("--optimize", action="store_true", help="ofrecer limpieza opcional con confirmación adicional; nunca necesaria para Home")
    args = p.parse_args()
    if not args.command:
        menu()
        return
    {"status": cmd_status, "install": cmd_install, "apps": cmd_apps, "uninstall": cmd_uninstall}[args.command](args)


if __name__ == "__main__":
    main()
