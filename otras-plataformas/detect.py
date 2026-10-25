#!/usr/bin/env python3
"""Find TVs on the local network and say which HorizonX build fits each one.

  python3 platforms/detect.py            scan (SSDP/DIAL) and probe each TV
  python3 platforms/detect.py 192.168.1.40

Read-only: only public discovery and status endpoints are queried. Nothing is installed.
"""
from __future__ import annotations

import json
import re
import socket
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ssdp(timeout=3):
    """All SSDP answers: {ip: [headers...]}"""
    found: dict[str, list[str]] = {}
    for st in (b"ssdp:all", b"roku:ecp", b"urn:dial-multiscreen-org:service:dial:1"):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        s.settimeout(timeout)
        s.sendto(b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\nST: ' + st + b"\r\n\r\n",
                 ("239.255.255.250", 1900))
        try:
            while True:
                data, (ip, _) = s.recvfrom(4096)
                found.setdefault(ip, []).append(data.decode("utf-8", "replace"))
        except (socket.timeout, TimeoutError):
            pass
        finally:
            s.close()
    return found


def get(url, timeout=3):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def port_open(ip, port, timeout=0.8):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def describe(ip, headers=()):
    text = "\n".join(headers)
    samsung = get(f"http://{ip}:8001/api/v2/")
    if samsung:
        d = json.loads(samsung).get("device", {})
        return {"ip": ip, "platform": "samsung-tizen", "name": d.get("name"), "model": d.get("modelName"),
                "detail": f"{d.get('OS', 'Tizen')} · modo desarrollador {'activado' if str(d.get('developerMode')) == '1' else 'desactivado'}",
                "next": "platforms/samsung-tizen/installer/horizonx_tizen.py"}
    roku = get(f"http://{ip}:8060/query/device-info")
    if roku:
        r = {c.tag: c.text for c in ET.fromstring(roku)}
        return {"ip": ip, "platform": "roku-os", "name": r.get("user-device-name") or r.get("friendly-device-name"),
                "model": f"{r.get('model-name')} ({r.get('model-number')})", "detail": f"Roku OS {r.get('software-version')}",
                "next": "platforms/roku-os/installer/horizonx_roku.py"}
    # Hisense / Toshiba VIDAA: the RemoteNOW MQTT port, and no Android ADB.
    if port_open(ip, 36669) and not port_open(ip, 5555):
        return {"ip": ip, "platform": "hisense-vidaa", "name": None, "model": None,
                "detail": "VIDAA (Linux): app web experimental, no reemplaza el inicio",
                "next": "platforms/hisense-vidaa/installer/horizonx_vidaa.py"}
    location = re.search(r"LOCATION:\s*(\S+)", text, re.I)
    info = {}
    if location:
        xml = get(location.group(1))
        if xml:
            try:
                root = ET.fromstring(xml)
                for el in root.iter():
                    tag = el.tag.split("}")[-1]
                    if tag in ("manufacturer", "modelName", "friendlyName") and el.text and tag not in info:
                        info[tag] = el.text.strip()
            except ET.ParseError:
                pass
    maker = (info.get("manufacturer") or "").lower()
    if "lg" in maker or port_open(ip, 3000) and port_open(ip, 3001):
        return {"ip": ip, "platform": "lg-webos", "name": info.get("friendlyName"), "model": info.get("modelName"),
                "detail": "webOS: no instala APK ni WGT", "next": "No compatible por ahora (ver docs)"}
    adb = port_open(ip, 5555)
    amazon = "amazon" in maker or "fire" in (info.get("modelName") or "").lower()
    if amazon or adb or "dial" in text.lower():
        platform = "amazon-fireos" if amazon else "android-tv"
        return {"ip": ip, "platform": platform, "name": info.get("friendlyName"), "model": info.get("modelName"),
                "detail": ("ADB abierto (5555)" if adb else "ADB cerrado: activar depuración"),
                "next": "platforms/amazon-fireos/installer/horizonx_fire.py" if amazon else "companion/HorizonX.sh"}
    return None


def main():
    targets = {ip: [] for ip in sys.argv[1:]} or ssdp()
    tvs = [d for d in (describe(ip, h) for ip, h in targets.items()) if d]
    if not tvs:
        print("No encontré televisores. Comprueba que estén encendidos y en la misma red, o pasa la IP.")
        return 1
    for d in tvs:
        print(f"\n{d['ip']}  {d['name'] or ''}\n  Plataforma: {d['platform']}\n  Modelo: {d['model'] or '?'}\n  {d['detail']}\n  Siguiente paso: {d['next']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
