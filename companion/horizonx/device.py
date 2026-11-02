"""Read-only discovery, exact enabled state and capability inventory. No UI launches."""
from __future__ import annotations
import datetime as dt
import hashlib
import re
from .adb import COMPONENT, Error, package, help_commands

PROPERTIES = {
    "manufacturer": "ro.product.manufacturer", "brand": "ro.product.brand",
    "model": "ro.product.model", "device": "ro.product.device", "product": "ro.product.name",
    "android": "ro.build.version.release", "sdk": "ro.build.version.sdk",
    "firmware": "ro.build.display.id", "fingerprint": "ro.build.fingerprint",
    "security_patch": "ro.build.version.security_patch", "abi": "ro.product.cpu.abilist",
    "commercial_model": "ro.product.vendor.model",
}
BRANDS = {
    "Philips": ("philips", "tp vision", "tpv"), "Sony": ("sony", "bravia"),
    "TCL": ("tcl",), "Xiaomi": ("xiaomi", "redmi"), "Hisense": ("hisense",),
    "Sharp": ("sharp",), "Toshiba": ("toshiba",), "Realme": ("realme",),
    "Thomson": ("thomson",), "Google": ("google",), "NVIDIA": ("nvidia",),
}

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def manufacturer(data):
    words = " ".join(str(data.get(k, "")) for k in ("manufacturer", "brand", "model")).lower()
    for brand, aliases in BRANDS.items():
        if any(a in words for a in aliases):
            return brand
    return "Otro Android"

def identity(adb):
    raw = adb.shell("getprop")
    props = dict(re.findall(r"^\[([^\]]+)\]: \[(.*)\]$", raw, re.M))
    data = {k: props.get(v, "") for k, v in PROPERTIES.items()}
    serial = props.get("ro.serialno") or props.get("ro.boot.serialno") or ""
    data["hardware_id"] = hashlib.sha256(serial.encode()).hexdigest() if serial else None
    try:
        data["sdk"] = int(data["sdk"])
        user = adb.shell("am", "get-current-user").strip()
        if not re.fullmatch(r"\d+", user):
            raise ValueError()
        data["user"] = int(user)
    except ValueError as e:
        raise Error("No se pudo identificar Android o el usuario actual. webOS y Tizen no son compatibles con ADB Android.") from e
    data["family"] = manufacturer(data)
    features = adb.shell("pm", "list", "features")
    data["android_tv"] = any(f in features for f in ("android.software.leanback", "android.hardware.type.television"))
    data["transport"] = adb.serial
    # Stable hardware ID survives a change of Wi-Fi ADB address. Missing ID => analysis only.
    return data

def binding(device):
    return {k: device.get(k) for k in ("hardware_id", "manufacturer", "model", "device", "fingerprint", "sdk", "user")}

def home(adb, user):
    answer = adb.shell("cmd", "package", "resolve-activity", "--brief", "--user", str(user),
                       "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
    result = [line.strip() for line in answer.splitlines() if COMPONENT.fullmatch(line.strip())]
    return result[-1] if result else None

def home_handlers(adb, user):
    answer = adb.shell("cmd", "package", "query-activities", "--brief", "--user", str(user),
                       "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
    return sorted({line.strip().split("/")[0] for line in answer.splitlines() if COMPONENT.fullmatch(line.strip())})

def names(answer):
    result = set()
    for line in answer.splitlines():
        if line.startswith("package:"):
            candidate = line[8:].split()[0]
            result.add(package(candidate))
    return sorted(result)

def package_state(adb, name, user):
    name = package(name)
    raw = adb.shell("dumpsys", "package", name)
    # Only the named package's own Package section; SharedUser and resolver entries are not state.
    match = re.search(r"(?m)^\s*Package \[" + re.escape(name) + r"\][^\n]*:\s*\n", raw)
    if not match:
        raise Error(f"No se pudo leer el estado de {name}")
    block = raw[match.end():]
    block = re.split(r"(?m)^\s*Package \[", block, maxsplit=1)[0]
    user_match = re.search(r"(?m)^\s*User " + str(user) + r":([^\n]*)", block)
    if not user_match:
        raise Error(f"Sin estado del usuario {user} para {name}")
    line = user_match.group(1)
    def value(pattern, default=None):
        m = re.search(pattern, block, re.M)
        return m.group(1).strip() if m else default
    enabled = re.search(r"\benabled=(\d+)\b", line)
    # Android 14 dumps ApplicationInfo.appId; older builds call this same base ID userId.
    # Preserve the existing field semantics (base app ID, not user*100000 + appId).
    legacy_uid = value(r"^\s*userId=(\d+)")
    app_id = value(r"^\s*appId=(\d+)")
    if legacy_uid and app_id and legacy_uid != app_id:
        raise Error(f"Identidad appId/userId contradictoria de {name}")
    uid = app_id or legacy_uid
    version = value(r"^\s*versionCode=(\d+)")
    if not enabled or int(enabled[1]) not in range(5) or not uid or not version:
        raise Error(f"Estado incompleto de {name}")
    perms = re.search(r"(?ms)^\s*requested permissions:\s*\n(.*?)(?=^\s*(?:install permissions:|runtime permissions:|User \d+:)|\Z)", block)
    permissions = sorted(set(re.findall(r"(?:android|com|org)\.[\w.]+", perms[1]))) if perms else []
    # Manifest-level enablement is separate from the per-user DEFAULT override.
    return {
        "name": name, "enabled": int(enabled[1]), "installed": "installed=true" in line,
        "hidden": "hidden=true" in line, "suspended": "suspended=true" in line,
        "uid": int(uid), "version": version,
        "code_path": value(r"^\s*codePath=(.*)"),
        "updated": value(r"^\s*lastUpdateTime=(.*)"),
        "signatures": value(r"^\s*signatures=.*?signatures:\[([^\]]+)\]"),
        "shared_uid": bool(re.search(r"^\s*sharedUser(?:Id)?=", block, re.M)),
        "persistent": bool(re.search(r"\bPERSISTENT\b", block)),
        "permissions": permissions,
        "components": sorted(set(re.findall(re.escape(name) + r"/[A-Za-z0-9_.$]+", raw)))[:200],
    }

def inventory(adb):
    device = identity(adb)
    user = device["user"]
    packages = names(adb.shell("pm", "list", "packages", "--user", str(user)))
    if not packages:
        raise Error("Inventario vacío; análisis interrumpido")
    system = set(names(adb.shell("pm", "list", "packages", "-s", "--user", str(user))))
    disabled = names(adb.shell("pm", "list", "packages", "-d", "--user", str(user)))
    details, errors = {}, {}
    for name in packages:
        try:
            details[name] = {**package_state(adb, name, user), "system": name in system}
        except Error as e:
            errors[name] = str(e)
    capabilities = {"pm": adb.optional("pm", "help"), "services": adb.optional("dumpsys", "-l")}
    # Store service names only, not account-bearing activity/service extras.
    services = capabilities["services"].get("value", "").splitlines()
    pm_commands = help_commands(capabilities["pm"].get("value", ""))
    result = {"schema": 1, "kind": "horizonx-analysis", "created": utc(), "device": device,
              "home": home(adb, user), "home_handlers": home_handlers(adb, user),
              "packages": details, "unreadable": errors, "disabled": disabled,
              "services": [s.strip() for s in services if re.fullmatch(r"\s*[A-Za-z0-9_.-]+\s*", s)],
              "capabilities": {"disable_user": "disable-user" in pm_commands,
                               "default_state": "default-state" in pm_commands,
                               "enable": "enable" in pm_commands}}
    if binding(identity(adb)) != binding(device):
        raise Error("El dispositivo o usuario cambió durante el inventario")
    return result
