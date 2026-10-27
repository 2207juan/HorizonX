#!/usr/bin/env python3
"""HorizonX for Roku: find the Roku, check compatibility, install the development channel,
and open apps from the PC (ECP), which a Roku channel itself is not allowed to do.

  python3 horizonx_roku.py                    menu
  python3 horizonx_roku.py status   [--roku IP]
  python3 horizonx_roku.py install  [--roku IP] [--password PASS]
  python3 horizonx_roku.py apps     [--roku IP]
  python3 horizonx_roku.py launch NAME [--roku IP]
  python3 horizonx_roku.py remove   [--roku IP] [--password PASS]

Standard library only. Nothing on the Roku is changed except installing/removing the HorizonX
development channel through Roku's own Development Application Installer.
"""
from __future__ import annotations

import argparse
import getpass
import json
import re
import socket
import sys
import urllib.error
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = json.loads((HERE.parent / "data" / "devices.json").read_text(encoding="utf-8"))


def say(t=""):
    print(t, flush=True)


def ask(t):
    try:
        return input(t).strip()
    except EOFError:
        return ""


def discover(timeout=3):
    """SSDP search for Roku's ECP service (roku:ecp)."""
    msg = (b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\n'
           b"ST: roku:ecp\r\nMX: 2\r\n\r\n")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.settimeout(timeout)
    s.sendto(msg, ("239.255.255.250", 1900))
    found = []
    try:
        while True:
            data, _ = s.recvfrom(2048)
            m = re.search(rb"LOCATION:\s*http://([\d.]+):(\d+)", data, re.I)
            if m and m.group(1).decode() not in found:
                found.append(m.group(1).decode())
    except (socket.timeout, TimeoutError):
        pass
    finally:
        s.close()
    return found


def ecp(ip, path, method="GET", port=8060):
    req = urllib.request.Request(f"http://{ip}:{port}{path}", method=method, data=b"" if method == "POST" else None)
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.read()


def device_info(ip):
    try:
        root = ET.fromstring(ecp(ip, "/query/device-info"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            sys.exit("El Roku rechaza consultas: Configuración → Sistema → Configuración avanzada del sistema → "
                     "Control por apps móviles → Acceso a la red: «Predeterminado» o «Permisivo».")
        raise
    return {child.tag: (child.text or "") for child in root}


def lookup(model):
    m = (model or "").upper()
    for d in DB["devices"]:
        if m in [x.upper() for x in d["model_numbers"]]:
            return d
    # Roku TVs report e.g. "C000X" family codes; retail TV models (e.g. 55R6E) are not in Roku's table.
    return None


def pick(ip=None):
    if ip:
        return ip
    say("Buscando Roku en tu red…")
    found = discover()
    if not found:
        ip = ask("No encontré ninguno. IP del Roku (Configuración → Red → Acerca de): ")
        return ip or sys.exit(1)
    if len(found) == 1:
        return found[0]
    for i, f in enumerate(found, 1):
        name = device_info(f).get("user-device-name") or f
        say(f"  {i}. {name} ({f})")
    n = ask("Número: ")
    return found[int(n) - 1] if n.isdigit() and 0 < int(n) <= len(found) else sys.exit(1)


def cmd_status(args):
    ip = pick(args.roku)
    info = device_info(ip)
    model = info.get("model-number", "")
    row = lookup(model)
    say(f"\n{info.get('user-device-name') or info.get('friendly-device-name') or 'Roku'} — {info.get('model-name')} ({model})")
    say(f"Roku OS {info.get('software-version')} (build {info.get('software-build')})  ·  {'Roku TV' if info.get('is-tv') == 'true' else 'reproductor'}")
    say(f"Modo desarrollador: {'activado' if info.get('developer-enabled') == 'true' else 'desactivado'}")
    if row:
        say(f"Base de datos: {row['product']} · {row['year'] or 's/f'} · {row['ram']} · estado Roku: {row['support']}")
        say("HorizonX: " + row["horizonx"])
    else:
        say("Modelo no listado en la base de datos de Roku; si recibe actualizaciones de Roku OS, el canal debería funcionar.")
    say("HorizonX aún no se ha probado físicamente en ningún Roku (solo en emulador).")
    return ip, info


def multipart(fields, file_field, filename, data):
    boundary = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    out += (f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            "Content-Type: application/zip\r\n\r\n").encode() + data + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return out, f"multipart/form-data; boundary={boundary}"


def installer(ip, password, fields, package=None):
    """Roku's Development Application Installer (port 80, HTTP digest, user rokudev)."""
    auth = urllib.request.HTTPDigestAuthHandler()
    auth.add_password("rokudev", f"http://{ip}/", "rokudev", password)
    opener = urllib.request.build_opener(auth)
    data = package.read_bytes() if package else b""
    body, ctype = multipart(fields, "archive", package.name if package else "", data)
    req = urllib.request.Request(f"http://{ip}/plugin_install", data=body, headers={"Content-Type": ctype}, method="POST")
    with opener.open(req, timeout=120) as r:
        html = r.read().decode("utf-8", "replace")
    msgs = re.findall(r"<font color=\"red\">(.*?)</font>|'text':\s*'([^']+)'", html)
    return " ".join(a or b for a, b in msgs).strip() or "OK"


def package_path():
    found = sorted(HERE.glob("HorizonX-Roku-*.zip")) + sorted((HERE.parents[2] / "dist").glob("HorizonX-Roku-*.zip"))
    return found[-1] if found else sys.exit("No encuentro HorizonX-Roku-x.y.z.zip junto al asistente.")


def developer_help():
    say("\nActiva el modo desarrollador una vez:")
    say("  1. Con el mando pulsa: Inicio ×3, Arriba ×2, Derecha, Izquierda, Derecha, Izquierda, Derecha (en menos de 10 s).")
    say("  2. Acepta el acuerdo, crea una contraseña y anota la dirección que muestra la pantalla.")
    say("  3. El Roku se reinicia. Vuelve a ejecutar este asistente.")
    say("El Roku tiene que estar vinculado a una cuenta Roku.")


def cmd_install(args):
    ip, info = cmd_status(args)
    if info.get("developer-enabled") != "true":
        developer_help()
        return
    pkg = package_path()
    password = args.password or getpass.getpass("Contraseña del modo desarrollador: ")
    try:
        result = installer(ip, password, {"mysubmit": "Install", "passwd": ""}, pkg)
    except urllib.error.HTTPError as e:
        sys.exit("Contraseña incorrecta." if e.code == 401 else f"El instalador del Roku respondió {e.code}.")
    say(f"Roku: {result}")
    say("\nListo. HorizonX aparece en el inicio del Roku.")
    say("Salvapantallas: Configuración → Tema → Salvapantallas → HorizonX.")
    say("Aviso: Roku solo admite un canal de desarrollo a la vez; instalar otro sustituye a HorizonX.")


def cmd_remove(args):
    ip = pick(args.roku)
    password = args.password or getpass.getpass("Contraseña del modo desarrollador: ")
    say(installer(ip, password, {"mysubmit": "Delete", "archive": ""}))


def apps(ip):
    root = ET.fromstring(ecp(ip, "/query/apps"))
    return [{"id": a.get("id"), "name": a.text or "", "type": a.get("type")} for a in root.findall("app")]


def cmd_apps(args):
    ip = pick(args.roku)
    for a in apps(ip):
        say(f"  {a['name']:<36} {a['id']}")


def cmd_launch(args):
    ip = pick(args.roku)
    want = args.name.lower()
    match = next((a for a in apps(ip) if a["id"] == args.name or a["name"].lower().startswith(want)), None)
    if not match:
        sys.exit(f"No encuentro «{args.name}» en este Roku.")
    ecp(ip, f"/launch/{match['id']}", "POST")
    say(f"Abriendo {match['name']}…")


def menu():
    say("HorizonX · Roku\n")
    items = {"1": ("¿Es compatible mi Roku?", cmd_status), "2": ("Instalar HorizonX", cmd_install),
             "3": ("Ver apps instaladas", cmd_apps), "4": ("Quitar HorizonX", cmd_remove)}
    while True:
        for k, (label, _) in items.items():
            say(f"{k}. {label}")
        say("0. Salir")
        c = ask("Opción: ")
        if c in ("0", ""):
            return
        if c in items:
            try:
                items[c][1](argparse.Namespace(roku=None, password=None))
            except (OSError, SystemExit) as e:
                say(str(e))
            say("")


def main():
    p = argparse.ArgumentParser(description="HorizonX para Roku")
    p.add_argument("command", nargs="?", choices=["status", "install", "apps", "launch", "remove"])
    p.add_argument("name", nargs="?")
    p.add_argument("--roku")
    p.add_argument("--password")
    p.add_argument("--port", type=int, default=8060, help=argparse.SUPPRESS)
    args = p.parse_args()
    if not args.command:
        menu()
        return
    {"status": cmd_status, "install": cmd_install, "apps": cmd_apps, "launch": cmd_launch, "remove": cmd_remove}[args.command](args)


if __name__ == "__main__":
    main()
