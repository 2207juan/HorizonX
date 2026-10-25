"""Experimental opt-in Private DNS. Requires an exact profile separately validated for DNS."""
from __future__ import annotations
import re
import secrets
from .adb import Error
from .device import identity, utc, binding
from .transactions import same_device, confirm, token

KEYS = ("private_dns_specifier", "private_dns_mode")

def settings(adb):
    raw = adb.shell("settings", "list", "global")
    values = dict(line.split("=", 1) for line in raw.splitlines() if "=" in line)
    return {k: values.get(k) for k in KEYS}

def write(adb, key, value):
    if key not in KEYS:
        raise Error("Clave DNS desconocida")
    if value is None:
        adb.shell("settings", "delete", "global", key)
    else:
        adb.shell("settings", "put", "global", key, value)

def plan(adb, store, db, hostname):
    if not isinstance(hostname, str) or len(hostname) > 253 or not re.fullmatch(r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}", hostname):
        raise Error("Usa un nombre de servidor DNS TLS, sin URL ni dirección IP")
    device = identity(adb)
    p = db.match(device)
    if not p or p.get("validation", {}).get("status") != "verified" or p.get("private_dns_verified") is not True or device["sdk"] < 28 or device["user"] != 0 or not device["hardware_id"]:
        raise Error("DNS: solo información. Esta combinación de modelo y firmware no tiene una prueba DNS verificada.")
    value = {"schema": 1, "kind": "horizonx-dns-plan", "id": "dns-plan-" + secrets.token_hex(8),
             "created": utc(), "device": device, "database_sha256": db.sha,
             "before": settings(adb), "after": {"private_dns_specifier": hostname.lower(), "private_dns_mode": "hostname"},
             "warning": "Puede interrumpir servicios y reproducción; no bloquea todos los anuncios. El proveedor recibe consultas DNS."}
    store.save(value["id"], value)
    return value

def recover(adb, store, journal):
    same_device(adb, journal["device"])
    errors = []
    recording_errors = []
    def persist():
        try:
            store.save(journal["id"], journal)
        except OSError as e:
            recording_errors.append(str(e))
    # Restore the mode first, then its specifier; preserve absent keys with delete, not a fake default.
    for key in reversed(KEYS):
        if key not in journal.get("attempted", []):
            continue
        try:
            now = settings(adb)[key]
            if now not in (journal["before"][key], journal["after"][key]):
                raise Error("La configuración DNS fue modificada por otra operación")
            if now != journal["before"][key]:
                write(adb, key, journal["before"][key])
            if settings(adb)[key] != journal["before"][key]:
                raise Error("La configuración no se restauró")
        except (Error, OSError) as e:
            errors.append({"key": key, "error": str(e)})
        persist()
    journal["status"] = "recovery-required" if errors or recording_errors else "restored"
    journal["errors"] = errors
    persist()
    if recording_errors:
        journal["status"] = "recovery-required"
        journal["recording_errors"] = recording_errors
    return journal

def apply(adb, store, db, plan_id, approval):
    with store.lock():
        p = store.load(plan_id)
        if p.get("kind") != "horizonx-dns-plan":
            raise Error("Plan DNS inválido")
        confirm(token("DNS-EXPERIMENTAL", p), approval)
        same_device(adb, p["device"])
        profile = db.match(p["device"])
        if db.sha != p["database_sha256"] or not profile or not profile.get("private_dns_verified") or profile.get("validation", {}).get("status") != "verified":
            raise Error("Perfil DNS cambiado")
        if settings(adb) != p["before"]:
            raise Error("La configuración DNS cambió; genera un plan nuevo")
        for name in store.records("dns-transaction-"):
            previous = store.load(name)
            if previous["plan_id"] == plan_id or (binding(previous["device"]) == binding(p["device"]) and previous.get("status") != "restored"):
                raise Error("Restaura la operación DNS anterior antes de continuar")
        j = {**p, "kind": "horizonx-dns-transaction", "id": "dns-transaction-" + secrets.token_hex(8), "plan_id": plan_id,
             "status": "applying", "attempted": []}
        store.save(j["id"], j)
        try:
            for key in KEYS:
                same_device(adb, j["device"])
                if settings(adb)[key] != j["before"][key]:
                    raise Error("Conflicto de configuración DNS")
                j["attempted"].append(key); store.save(j["id"], j)
                write(adb, key, j["after"][key])
                if settings(adb)[key] != j["after"][key]:
                    raise Error("No se pudo verificar el valor DNS")
            j["status"] = "applied"; store.save(j["id"], j)
            return j
        except (Error, KeyboardInterrupt, OSError) as e:
            j["error"] = str(e) or "Interrumpido"
            try:
                store.save(j["id"], j)
            except OSError:
                pass
            return recover(adb, store, j)

def restore(adb, store, record_id, approval):
    with store.lock():
        j = store.load(record_id)
        if j.get("kind") != "horizonx-dns-transaction":
            raise Error("Registro DNS inválido")
        confirm(token("RESTAURAR-DNS", j), approval)
        return recover(adb, store, j)
