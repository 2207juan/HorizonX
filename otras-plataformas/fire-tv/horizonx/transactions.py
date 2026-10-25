"""Opt-in reversible per-user state changes with write-ahead journaling and rollback."""
from __future__ import annotations
import datetime as dt
import secrets
from .adb import Error, package
from .device import binding, home, identity, inventory, package_state, utc
from .profiles import analyze, protected_reason
from .store import digest

RESTORE_COMMAND = {0: "default-state", 1: "enable", 2: "disable", 3: "disable-user", 4: "disable-until-used"}

def token(action, record):
    return f"{action}-{digest(record)[:16]}"

def confirm(expected, approval):
    if approval != expected:
        raise Error(f"No hay aprobación para esta operación. Revisa el documento y usa --approve {expected}")

def same_device(adb, device):
    current = identity(adb)
    if not device.get("hardware_id") or binding(current) != binding(device):
        raise Error("Dispositivo, firmware o usuario distintos; no se ejecutará ningún cambio")
    return current

def same_package(before, now):
    return all(before.get(k) == now.get(k) for k in ("name", "uid", "version", "code_path", "updated", "signatures", "shared_uid", "persistent", "permissions", "installed", "hidden", "suspended"))

def create_plan(adb, store, report, db, selected, mode="conservative"):
    if not selected or len(selected) != len(set(selected)):
        raise Error("Selecciona uno o más paquetes únicos")
    for name in selected:
        package(name)
    same_device(adb, report["device"])
    current = inventory(adb)
    if current["home"] != report["home"]:
        raise Error("Inicio cambió desde el análisis; genera un nuevo análisis")
    analysis = analyze(current, db, mode)
    if not analysis["writes_available"]:
        raise Error("Solo análisis: no hay perfil exacto verificado o faltan capacidades/estado fiables")
    entries = {p["name"]: p for p in analysis["packages"]}
    for name in selected:
        entry = entries.get(name)
        if not entry or not entry["eligible"]:
            raise Error(f"Paquete protegido o no apto: {name}")
        if not same_package(report["packages"].get(name, {}), current["packages"][name]) or report["packages"][name]["enabled"] != current["packages"][name]["enabled"]:
            raise Error(f"El estado de {name} cambió; repite el análisis")
        # A selected action cannot disable a declared dependency of any other reviewed entry.
        profile = db.match(current["device"])
        if name in profile.get("protected_packages", []) or any(name in e.get("dependencies", []) for e in profile.get("packages", [])):
            raise Error(f"Dependencia o paquete protegido por el perfil: {name}")
    plan = {"schema": 1, "kind": "horizonx-plan", "id": "plan-" + secrets.token_hex(8),
            "created": utc(), "expires": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=30)).isoformat(),
            "device": current["device"], "home": current["home"], "database_sha256": db.sha,
            "profile": analysis["profile"], "mode": mode,
            "selected": selected, "before": current,
            "actions": [{"name": n, "before": current["packages"][n], "after_enabled": 3,
                         "impact": entries[n]["classification"]["impact"],
                         "inverse": ["pm", RESTORE_COMMAND[current["packages"][n]["enabled"]], "--user", "0", n]}
                        for n in selected]}
    store.save(plan["id"], plan)
    return plan

def set_state(adb, name, enabled, user):
    package(name)
    if enabled not in RESTORE_COMMAND or user != 0:
        raise Error("Estado o usuario no permitido")
    adb.shell("pm", RESTORE_COMMAND[enabled], "--user", str(user), name)
    if package_state(adb, name, user)["enabled"] != enabled:
        raise Error(f"El televisor no conservó el estado solicitado para {name}")

def validate_journal(journal):
    if journal.get("schema") != 1 or journal.get("kind") != "horizonx-transaction" or not journal.get("device", {}).get("hardware_id"):
        raise Error("Diario no reconocido")
    if journal["device"].get("user") != 0:
        raise Error("Usuario no soportado")
    seen = set()
    for action in journal.get("actions", []):
        name = package(action["name"])
        if name in seen or action["before"].get("name") != name or action["before"].get("enabled") not in (0, 1) or action.get("after_enabled") != 3:
            raise Error("Diario de estados inválido")
        seen.add(name)


def restore_internal(adb, store, journal):
    validate_journal(journal)
    failures = []
    recording_errors = []
    def persist():
        try:
            store.save(journal["id"], journal)
        except OSError as e:
            # Original write-ahead record already exists. Try its approved inverse even if
            # the PC disk became full after the forward command; do not abandon recovery.
            recording_errors.append(str(e))
    for action in reversed(journal["actions"]):
        if action.get("status") in ("prepared", "restored"):
            continue
        try:
            same_device(adb, journal["device"])
            now = package_state(adb, action["name"], 0)
            if not same_package(action["before"], now):
                raise Error("Versión, identidad o estado del paquete cambió")
            if now["enabled"] == action["before"]["enabled"]:
                action["status"] = "restored"
            elif now["enabled"] != action["after_enabled"]:
                raise Error("Conflicto: el estado fue cambiado fuera de esta operación")
            else:
                action["status"] = "restoring"
                persist()
                set_state(adb, action["name"], action["before"]["enabled"], 0)
                action["status"] = "restored"
                action.pop("error", None)
        except (Error, OSError) as e:
            action["error"] = str(e)
            failures.append({"name": action["name"], "error": str(e)})
        persist()
    journal["status"] = "recovery-required" if failures or recording_errors else "restored"
    journal["finished"] = utc()
    journal["recovery_errors"] = failures
    persist()
    if recording_errors:
        journal["status"] = "recovery-required"
        journal["recording_errors"] = recording_errors
    return journal

def apply(adb, store, db, plan_id, approval, measure=None):
    with store.lock():
        plan = store.load(plan_id)
        if plan.get("kind") != "horizonx-plan":
            raise Error("No es un plan")
        confirm(token("APLICAR", plan), approval)
        if dt.datetime.fromisoformat(plan["expires"]) < dt.datetime.now(dt.timezone.utc):
            raise Error("El plan caducó; vuelve a analizar")
        if plan["database_sha256"] != db.sha:
            raise Error("La base de perfiles cambió; revisa un plan nuevo")
        same_device(adb, plan["device"])
        current = inventory(adb)
        analysis = analyze(current, db, plan["mode"])
        allowed = {e["name"] for e in analysis["packages"] if e["eligible"]}
        if not analysis["writes_available"] or set(plan["selected"]) - allowed or current["home"] != plan["home"]:
            raise Error("El plan ya no es aplicable")
        if current["home_handlers"] != plan["before"]["home_handlers"]:
            raise Error("Los componentes de Inicio cambiaron")
        for action in plan["actions"]:
            now = current["packages"][action["name"]]
            if not same_package(action["before"], now) or action["before"]["enabled"] != now["enabled"]:
                raise Error("Estado previo distinto al aprobado")
        for record in store.records():
            previous = store.load(record)
            if binding(previous.get("device", {})) == binding(plan["device"]) and previous.get("status") not in ("restored", "applied"):
                raise Error("Hay una operación incompleta; restaura su diario primero")
            if previous.get("plan_id") == plan_id:
                raise Error("Un plan no puede ejecutarse dos veces")
        from copy import deepcopy
        journal = {"schema": 1, "kind": "horizonx-transaction", "id": "transaction-" + secrets.token_hex(8),
                   "plan_id": plan_id, "created": utc(), "device": plan["device"], "home": plan["home"],
                   "status": "prepared", "actions": deepcopy(plan["actions"]), "baseline": current,
                   "measurement_before": measure(adb) if measure else None}
        for a in journal["actions"]:
            a["status"] = "prepared"
        # No command can mutate the TV before this durable original state exists.
        store.save(journal["id"], journal)
        try:
            journal["status"] = "applying"
            store.save(journal["id"], journal)
            for action in journal["actions"]:
                same_device(adb, journal["device"])
                if home(adb, 0) != journal["home"]:
                    raise Error("El launcher predeterminado cambió; operación interrumpida")
                now = package_state(adb, action["name"], 0)
                if not same_package(action["before"], now) or action["before"]["enabled"] != now["enabled"]:
                    raise Error("Conflicto antes de modificar el paquete")
                action["status"] = "attempting"
                store.save(journal["id"], journal)
                set_state(adb, action["name"], 3, 0)
                action["status"] = "applied"
                store.save(journal["id"], journal)
            # Verify the whole batch, including packages a vendor may re-enable immediately.
            same_device(adb, journal["device"])
            for a in journal["actions"]:
                now = package_state(adb, a["name"], 0)
                if not same_package(a["before"], now) or now["enabled"] != 3:
                    raise Error("La verificación final del lote no coincide")
            if home(adb, 0) != journal["home"]:
                raise Error("Inicio cambió durante la operación")
            journal["status"] = "applied"
            journal["finished"] = utc()
            journal["measurement_after"] = measure(adb) if measure else None
            store.save(journal["id"], journal)
            return journal
        except (Error, OSError, KeyboardInterrupt) as e:
            journal["error"] = str(e) or "Operación interrumpida"
            journal["status"] = "rolling-back"
            try:
                store.save(journal["id"], journal)
            except OSError:
                pass  # The durable attempting record still identifies the inverse.
            result = restore_internal(adb, store, journal)
            # Keep the failure visible even when automatic rollback succeeded.
            if result["status"] == "restored":
                result["status"] = "restored"
                result["outcome"] = "apply-failed-rolled-back"
                store.save(result["id"], result)
            return result

def restore(adb, store, transaction_id, approval):
    with store.lock():
        journal = store.load(transaction_id)
        validate_journal(journal)
        confirm(token("RESTAURAR", journal), approval)
        same_device(adb, journal["device"])
        return restore_internal(adb, store, journal)

def recovery_commands(journal):
    validate_journal(journal)
    return [["pm", RESTORE_COMMAND[a["before"]["enabled"]], "--user", "0", a["name"]]
            for a in reversed(journal["actions"]) if a.get("status") not in ("prepared", "restored")]
