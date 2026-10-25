"""Explicit APK installation only. Never changes Home, disables an app or opens a UI."""
from __future__ import annotations
import hashlib
from pathlib import Path
import re
import secrets
from .adb import Error, run
from .device import identity, home, package_state, utc
from .transactions import confirm, token, same_device
from .store import load_json

PACKAGE = "tv.lightos"  # stable update/data identity across the public rename

def inspect(apk, apksigner, aapt2, release_file=None):
    apk = Path(apk).resolve()
    release = load_json(release_file or Path(__file__).resolve().parents[1] / "release.json")
    sha = hashlib.sha256(apk.read_bytes()).hexdigest()
    if sha != release["apk_sha256"]:
        raise Error("El APK no corresponde a esta distribución")
    signer = run([apksigner, "verify", "--print-certs", apk])
    certs = re.findall(r"Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)", signer)
    if len(certs) != 1 or certs[0].lower() != release["certificate_sha256"].lower():
        raise Error("Firma del APK inesperada")
    badging = run([aapt2, "dump", "badging", apk])
    info = re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging)
    if not info or info[1] != PACKAGE or int(info[2]) != release["version_code"] or info[3] != release["version"]:
        raise Error("Identidad o versión del APK inesperada")
    if not re.search(r"^application-label:'HorizonX'$", badging, re.M):
        raise Error("El APK no tiene la etiqueta pública HorizonX esperada")
    if not re.search(r"^launchable-activity:.*label='HorizonX'", badging, re.M):
        raise Error("La actividad de acceso no tiene la etiqueta HorizonX esperada")
    return {"apk": str(apk), "sha256": sha, "certificate_sha256": certs[0].lower(),
            "package": PACKAGE, "version_code": int(info[2]), "version": info[3]}

def plan(adb, store, apk, apksigner, aapt2):
    artifact = inspect(apk, apksigner, aapt2)
    device = identity(adb)
    if not device.get("android_tv") or device["sdk"] < 26 or device["user"] != 0 or not device.get("hardware_id"):
        raise Error("Instalación asistida requiere Android TV 8+, usuario 0 e identidad de dispositivo disponible")
    h = home(adb, 0)
    if not h:
        raise Error("No se pudo guardar el Inicio actual")
    existing = adb.shell("pm", "list", "packages", "--user", "0", PACKAGE).splitlines()
    before = package_state(adb, PACKAGE, 0) if "package:" + PACKAGE in existing else None
    if before and int(before["version"]) > artifact["version_code"]:
        raise Error("No se admiten bajadas de versión")
    result = {"schema": 1, "kind": "horizonx-install-plan", "id": "install-plan-" + secrets.token_hex(8),
              "created": utc(), "device": device, "home": h, "artifact": artifact, "before": before,
              "note": "La instalación o actualización no elige Inicio. Conserva datos; no incluye una copia completa de datos privados de Android."}
    store.save(result["id"], result)
    return result

def install(adb, store, plan_id, approval, apksigner, aapt2):
    with store.lock():
        p = store.load(plan_id)
        if p.get("kind") != "horizonx-install-plan":
            raise Error("Plan de instalación inválido")
        confirm(token("INSTALAR", p), approval)
        same_device(adb, p["device"])
        if home(adb, 0) != p["home"]:
            raise Error("Inicio cambió desde la preparación")
        if inspect(p["artifact"]["apk"], apksigner, aapt2) != p["artifact"]:
            raise Error("El APK cambió")
        installed = "package:" + PACKAGE in adb.shell("pm", "list", "packages", "--user", "0", PACKAGE).splitlines()
        now = package_state(adb, PACKAGE, 0) if installed else None
        if now != p["before"]:
            raise Error("La instalación previa cambió; prepara un plan nuevo")
        record_id = "installation-" + secrets.token_hex(8)
        j = {**p, "id": record_id, "kind": "horizonx-installation", "status": "prepared", "old_apks": []}
        folder = store.root / (record_id + "-backup")
        folder.mkdir(mode=0o700)
        if now:
            for i, line in enumerate(adb.shell("pm", "path", PACKAGE).splitlines()):
                if not line.startswith("package:/"):
                    raise Error("No se pudo localizar la instalación anterior")
                destination = folder / f"previous-{i}.apk"
                adb.command("pull", line[8:], str(destination), timeout=120)
                certs = re.findall(r"Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)", run([apksigner, "verify", "--print-certs", destination]))
                if len(certs) != 1 or certs[0].lower() != p["artifact"]["certificate_sha256"]:
                    raise Error("La aplicación instalada tiene otra firma; no se reemplazará")
                j["old_apks"].append({"file": str(destination), "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
            if not j["old_apks"]:
                raise Error("No se obtuvo una copia del APK anterior")
        store.save(record_id, j)
        try:
            same_device(adb, p["device"])
            j["status"] = "installing"; store.save(record_id, j)
            output = adb.command("install", "-r", "--user", "0", p["artifact"]["apk"], timeout=180)
            if "Success" not in output:
                raise Error("Android no confirmó la instalación")
            after = package_state(adb, PACKAGE, 0)
            if after["version"] != str(p["artifact"]["version_code"]):
                raise Error("La versión instalada no coincide")
            j["home_unchanged"] = home(adb, 0) == p["home"]
            j["status"] = "installed" if j["home_unchanged"] else "review-required"
            j["after"] = after
        except (Error, OSError, KeyboardInterrupt) as e:
            j["status"] = "review-required"; j["error"] = str(e) or "Interrumpido"
        store.save(record_id, j)
        return j
