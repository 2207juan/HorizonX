"""Reviewed exact model/firmware profiles; unknown packages fail closed."""
from __future__ import annotations
from pathlib import Path
from .adb import Error, package
from .store import digest, load_json

ROOT = Path(__file__).resolve().parents[1] / "profiles"
CATEGORIES = {"manufacturer_ads", "recommendations", "optional_telemetry", "promotional_app", "verified_duplicate"}
# Entire namespaces are protected where they contain inseparable platform/OEM dependencies.
PROTECTED_PREFIXES = ("android", "com.android.", "com.google.", "org.droidtv.", "com.mediatek.",
                      "com.realtek.", "com.netflix.", "com.widevine.", "tv.lightos")
PROTECTED_NAMES = {"com.hisense.tv.smartsense", "com.vt.tv.smartsense.ui", "com.vt.tv.aiot",
                   "org.droidtv.ambisvc", "com.amazon.amazonvideo.livingroom", "com.disney.disneyplus",
                   "com.apple.atve.androidtv.appletv", "com.tcl.tv", "com.tcl.tvinput",
                   "com.tcl.system.server", "com.tcl.settings", "com.tcl.autopair",
                   "com.tcl.tcl_bt_rcu_service", "com.hisense.tv.smartservice"}
ESSENTIAL_PERMISSIONS = {"android.permission.TV_INPUT_HARDWARE", "android.permission.TV_VIRTUAL_REMOTE_CONTROLLER",
    "android.permission.REBOOT", "android.permission.RECOVERY", "android.permission.MASTER_CLEAR",
    "android.permission.INSTALL_PACKAGES", "android.permission.DELETE_PACKAGES",
    "android.permission.WRITE_SECURE_SETTINGS", "android.permission.MANAGE_USERS",
    "android.permission.BLUETOOTH_PRIVILEGED", "android.permission.NETWORK_STACK",
    "android.permission.CONNECTIVITY_INTERNAL", "android.permission.HDMI_CEC",
    "android.permission.MODIFY_AUDIO_ROUTING", "android.permission.BIND_ACCESSIBILITY_SERVICE",
    "android.permission.BIND_INPUT_METHOD", "android.permission.BIND_TV_INPUT"}
FUNCTION_CHECKS = {"boot", "remote", "bluetooth", "wifi", "ethernet", "hdmi", "cec", "picture", "sound",
    "drm", "netflix", "play_store", "installer", "keyboard", "accessibility", "updates", "recovery", "restore"}

class Database:
    def __init__(self, document=None):
        self.data = document if document is not None else load_json(ROOT / "compatibility.json")
        if self.data.get("schema") != 1:
            raise Error("Versión de perfiles desconocida")
        self.sha = digest(self.data)
        ids = set()
        for p in self.data.get("profiles", []):
            if not p.get("id") or p["id"] in ids:
                raise Error("Perfil sin identificador único")
            ids.add(p["id"])
            if p.get("validation", {}).get("status") == "verified":
                if not all(p.get(k) for k in ("manufacturer", "models", "firmware_fingerprints", "sdk")):
                    raise Error("Un perfil verificado requiere fabricante, modelo, SDK y fingerprint exactos")
                if any("*" in v for v in p["models"] + p["firmware_fingerprints"]):
                    raise Error("No se permiten comodines en perfiles verificados")
                validation = p["validation"]
                if not validation.get("evidence") or not validation.get("tested_at") or not FUNCTION_CHECKS.issubset(set(validation.get("functional_checks", []))):
                    raise Error("Validación funcional o recuperación incompleta")
            for e in p.get("packages", []):
                package(e["name"])
                if e.get("category") not in CATEGORIES or e.get("risk") not in ("minimal", "low", "medium", "high"):
                    raise Error("Clasificación de paquete inválida")
                if e.get("restore") != "previous_enabled_state":
                    raise Error("El perfil debe restaurar el estado previo exacto")

    def match(self, device):
        matches = [p for p in self.data.get("profiles", [])
                   if device.get("manufacturer", "").casefold() == p.get("manufacturer", "").casefold()
                   and device.get("model") in p.get("models", [])
                   and device.get("sdk") in p.get("sdk", [])
                   and device.get("fingerprint") in p.get("firmware_fingerprints", [])]
        if len(matches) > 1:
            raise Error("Perfiles exactos ambiguos")
        return matches[0] if matches else None

    def observations(self, report):
        # Documentation is independent from action eligibility: matching a package
        # from another firmware never upgrades it into a safe recommendation.
        data = load_json(ROOT / "observations.json")
        result = []
        for e in data["entries"]:
            if e["manufacturer_family"].casefold() != report["device"].get("family", "").casefold():
                continue
            state = report["packages"].get(e["name"])
            if state:
                result.append({**e, "eligible": False, "protected_reason": protected_reason(state, report),
                               "current_firmware_validated": False})
        return result

    def references(self, device, installed):
        result = []
        refs = load_json(ROOT / "community-references.json")["references"]
        for ref in refs:
            if ref["manufacturer"].casefold() != device.get("family", "").casefold():
                continue
            overlap = sorted(set(ref["packages"]) & set(installed))
            if overlap:
                result.append({"id": ref["id"], "source": ref["source"], "overlapping_names": overlap,
                               "status": "external-reference-only", "eligible": False})
        return result

def protected_reason(state, report):
    name = state["name"]
    if name in PROTECTED_NAMES or name.startswith(PROTECTED_PREFIXES):
        return "Plataforma, reproducción o dependencia OEM protegida"
    if name in report.get("home_handlers", []) or name == (report.get("home") or "").split("/")[0]:
        return "Inicio del televisor o vía de recuperación"
    if state.get("uid", 0) < 10000 or state.get("shared_uid") or state.get("persistent"):
        return "UID del sistema, compartido o proceso persistente"
    if ESSENTIAL_PERMISSIONS & set(state.get("permissions", [])):
        return "Permisos asociados a funciones esenciales"
    if not state.get("installed") or state.get("suspended") or state.get("hidden"):
        return "Estado del paquete no apto para esta operación"
    return None

def analyze(report, db, mode="conservative"):
    if mode not in ("conservative", "balanced", "custom"):
        raise Error("Modo desconocido")
    profile = db.match(report["device"])
    verified = bool(profile and profile.get("validation", {}).get("status") == "verified")
    by_name = {p["name"]: p for p in profile.get("packages", [])} if profile else {}
    entries = []
    for name, state in sorted(report["packages"].items()):
        entry = by_name.get(name)
        reason = protected_reason(state, report)
        if not reason and profile and name in profile.get("protected_packages", []):
            reason = "Protegido por el perfil del dispositivo"
        if not reason and profile and any(name in e.get("dependencies", []) for e in profile.get("packages", [])):
            reason = "Dependencia documentada de otro componente"
        if not reason and not all(state.get(k) for k in ("version", "code_path", "updated", "signatures")):
            reason = "Identidad de instalación incompleta"
        if not reason and not entry:
            reason = "Función y dependencias sin verificar; se conserva"
        if not reason and not verified:
            reason = "Modelo y firmware sin validación de cambios"
        if not reason and (entry.get("validation") != "verified" or not entry.get("evidence") or
                           entry.get("dependencies_reviewed") is not True or not entry.get("impact") or
                           not entry.get("function") or not entry.get("version_codes") or
                           state["version"] not in entry["version_codes"]):
            reason = "Evidencia, versión o dependencias insuficientes"
        if not reason and any(d not in report["packages"] for d in entry.get("dependencies", [])):
            reason = "Falta una dependencia documentada"
        if not reason and (state["enabled"] not in (0, 1) or name in report.get("disabled", [])):
            reason = "Ya estaba deshabilitado; no se modifica"
        if not reason and mode == "conservative" and entry["risk"] != "minimal":
            reason = "Fuera del modo conservador"
        if not reason and mode == "balanced" and entry["risk"] not in ("minimal", "low"):
            reason = "Fuera del modo equilibrado"
        if not reason and entry["risk"] == "high":
            reason = "Riesgo alto; no disponible para deshabilitación"
        entries.append({"name": name, "eligible": not bool(reason), "reason": reason,
                        "classification": entry or None})
    device = report["device"]
    writable = verified and device.get("android_tv") and bool(device.get("hardware_id")) and device.get("user") == 0 and bool(report.get("home")) and not report.get("unreadable") and all(report.get("capabilities", {}).get(k) for k in ("disable_user", "default_state", "enable"))
    return {"schema": 1, "database_sha256": db.sha, "profile": profile["id"] if profile else None,
            "profile_status": "verified" if verified else "analysis-only", "mode": mode,
            "writes_available": bool(writable), "packages": entries,
            "documented_components_to_review": db.observations(report),
            "limitations": ["El reconocimiento de marca no verifica un modelo.",
                            "Las dependencias desconocidas se conservan.",
                            "La primera versión permite cambios solo en el usuario propietario 0."]}
