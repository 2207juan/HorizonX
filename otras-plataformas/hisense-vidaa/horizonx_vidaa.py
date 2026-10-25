#!/usr/bin/env python3
"""HorizonX for Hisense / Toshiba VIDAA: experimental installer from a PC on the same network.

  python3 horizonx_vidaa.py                 serve the app and the install page (needs admin/root: DNS on port 53)
  python3 horizonx_vidaa.py --app-url URL   install a copy of HorizonX hosted elsewhere instead

How it works (community method, not supported by Hisense): VIDAA only lets the page at
vidaahub.com call the TV's install function. This program answers DNS for vidaahub.com with this
PC's address (every other name is forwarded to a public DNS), serves an install page there, and
serves HorizonX itself. On the TV: set DNS 1 to this PC, open vidaahub.com in the browser, press
Install, then put the DNS back to automatic. Reported to fail on some 2025 VIDAA firmware.

Without --app-url, HorizonX is served from this PC, so it opens only while this program runs.
Nothing else on the TV is changed. Written for HorizonX (no third-party code).
"""
from __future__ import annotations

import argparse
import functools
import http.server
import socket
import socketserver
import struct
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = HERE.parent / "build" / "site"
HUB = "vidaahub.com"
APP_ID = "HorizonX_debug"


def local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("1.1.1.1", 53))
        return s.getsockname()[0]
    finally:
        s.close()


# ---------------------------------------------------------------- DNS
def qname(packet: bytes) -> tuple[str, int]:
    """Name asked in a DNS query and the offset right after the question."""
    labels, i = [], 12
    while packet[i]:
        n = packet[i]
        labels.append(packet[i + 1:i + 1 + n].decode("ascii", "replace"))
        i += n + 1
    return ".".join(labels).lower(), i + 5


def answer(packet: bytes, ip: str) -> bytes:
    """An A-record reply for the question in [packet] pointing to [ip]."""
    _, end = qname(packet)
    header = packet[:2] + b"\x81\x80" + packet[4:6] + b"\x00\x01\x00\x00\x00\x00"
    record = b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 60, 4) + socket.inet_aton(ip)
    return header + packet[12:end] + record


def dns_server(ip: str, upstream: str = "1.1.1.1") -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 53))
    while True:
        packet, client = sock.recvfrom(4096)
        try:
            name, _ = qname(packet)
            if name == HUB or name.endswith("." + HUB):
                sock.sendto(answer(packet, ip), client)
                continue
            up = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            up.settimeout(3)
            up.sendto(packet, (upstream, 53))
            sock.sendto(up.recvfrom(4096)[0], client)
            up.close()
        except (OSError, IndexError):
            continue


# ---------------------------------------------------------------- pages
INSTALL_PAGE = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>HorizonX</title>
<style>body{{background:#0a0c17;color:#f5f6fb;font:28px sans-serif;text-align:center;padding-top:160px}}
button{{font-size:32px;padding:20px 60px;border-radius:40px;border:0;margin:20px}}button:focus{{background:#fff;color:#111}}
#s{{color:#8e97ab;margin-top:30px}}</style></head><body>
<h1>HorizonX para VIDAA</h1><p>Se instalará como una app más en «Mis apps».</p>
<button id="i" autofocus>Instalar</button><button id="u">Quitar</button><div id="s"></div>
<script>
var s=document.getElementById('s');
function done(r){{s.textContent='Resultado: '+r+'. Ya puedes volver a poner el DNS en automático.';}}
document.getElementById('i').onclick=function(){{
  if(typeof Hisense_installApp!=='function'){{s.textContent='Este televisor no ofrece la función de instalación (firmware bloqueado).';return;}}
  Hisense_installApp('{app_id}','HorizonX','{icon}','{icon}','{icon}','{url}','store',done);
}};
document.getElementById('u').onclick=function(){{
  if(typeof Hisense_uninstallApp==='function')Hisense_uninstallApp('{app_id}',done);
}};
</script></body></html>"""


class Handler(http.server.SimpleHTTPRequestHandler):
    install_page = b""

    def do_GET(self):
        host = (self.headers.get("Host") or "").split(":")[0].lower()
        if host == HUB or host.endswith("." + HUB):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.install_page)
            return
        super().do_GET()

    def log_message(self, *args):
        pass


def main() -> int:
    p = argparse.ArgumentParser(description="HorizonX para VIDAA (experimental)")
    p.add_argument("--app-url", help="URL de una copia de HorizonX ya publicada (si no, se sirve desde este PC)")
    p.add_argument("--port", type=int, default=80)
    args = p.parse_args()
    ip = local_ip()
    site = SITE
    if not (site / "index.html").exists():
        # Public copy: the built app ships as HorizonX-VIDAA-*.zip next to this installer.
        packages = sorted(HERE.glob("HorizonX-VIDAA-*.zip"))
        if packages:
            import tempfile, zipfile
            site = Path(tempfile.mkdtemp(prefix="horizonx-vidaa-"))
            zipfile.ZipFile(packages[-1]).extractall(site)
    if not args.app_url and not (site / "index.html").exists():
        sys.exit("Falta la app: ejecuta primero platforms/hisense-vidaa/tools/build_vidaa.py")
    base = f"http://{ip}" + ("" if args.port == 80 else f":{args.port}")
    url = args.app_url or f"{base}/index.html"
    icon = f"{base}/img/icon.png"
    Handler.install_page = INSTALL_PAGE.format(app_id=APP_ID, icon=icon, url=url).encode("utf-8")
    try:
        threading.Thread(target=dns_server, args=(ip,), daemon=True).start()
        server = socketserver.ThreadingTCPServer(("0.0.0.0", args.port), functools.partial(Handler, directory=str(site)))
    except PermissionError:
        sys.exit("Hacen falta permisos de administrador (DNS en el puerto 53 y web en el 80). Usa sudo o «Ejecutar como administrador».")
    print(f"""HorizonX para VIDAA — experimental, sin garantía de Hisense.

En el televisor:
  1. Ajustes → Red → Configuración de red → DNS manual → DNS 1: {ip}
  2. Abre el navegador y entra en http://{HUB}
  3. Pulsa «Instalar». HorizonX aparecerá en «Mis apps».
  4. Vuelve a poner el DNS en automático.

{'HorizonX se abrirá desde este PC mientras este programa siga abierto.' if not args.app_url else 'HorizonX se abrirá desde ' + url}
Ctrl+C para terminar.""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
