"""Model-aware, reversible debloat: plan from tv-database.json, back up, disable, verify, restore.

Only `pm disable-user --user 0` is used, never uninstall. Every run writes a backup of the exact
previous state first, so `restore` can put each package back even after a HorizonX update.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from .adb import Adb, Error, package

PROFILES = Path(__file__).resolve().parents[1] / "profiles"
# Categories from an exact model profile that are applied by default. "optional" (streaming apps,
# Chromecast, Assistant…) is only offered: whether someone uses Netflix is their decision.
DEFAULT_CATEGORIES = {"telemetry", "ads", "demo"}
EXTRA_SAFE = {"recommended"}  # generic tier included in "recomendado" mode
# Never applied automatically even when many lists disable them: accessibility, fallbacks, data providers.
NEVER_AUTO = {"com.google.android.tts", "com.google.android.marvin.talkback", "com.android.dreams.basic",
              "com.android.providers.calendar", "com.android.providers.contacts", "com.android.backupconfirm",
              "com.android.sharedstoragebackup", "com.android.htmlviewer", "com.google.android.katniss",
              "com.google.android.tv.assistant", "com.android.dynsystem"}


def _now():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def database():
    return json.loads((PROFILES / "tv-database.json").read_text(encoding="utf-8"))


def platforms():
    return json.loads((PROFILES / "platforms.json").read_text(encoding="utf-8"))


def device_info(adb: Adb) -> dict:
    props = {}
    for line in adb.shell("getprop").splitlines():
        m = re.match(r"\[(.+?)\]: \[(.*)\]", line)
        if m:
            props[m.group(1)] = m.group(2)
    states = package_states(adb)
    launchable = set()
    for cat in ("android.intent.category.LEANBACK_LAUNCHER", "android.intent.category.LAUNCHER"):
        out = adb.shell("cmd", "package", "query-activities", "--brief", "-a", "android.intent.action.MAIN", "-c", cat)
        launchable |= {l.strip().split("/")[0] for l in out.splitlines() if "/" in l and not l.strip().startswith("priority")}
    for name, st in states.items():
        st["app"] = name in launchable
    if "com.amazon.tv.launcher" in states:
        platform = "fire-os"
    elif "com.google.android.apps.tv.launcherx" in states:
        platform = "google-tv"
    else:
        platform = "android-tv"
    return {
        "manufacturer": props.get("ro.product.manufacturer", ""),
        "brand": props.get("ro.product.brand", ""),
        "model": props.get("ro.product.model", ""),
        "device": props.get("ro.product.device", ""),
        "fingerprint": props.get("ro.build.fingerprint", ""),
        "sdk": int(props.get("ro.build.version.sdk", "0") or 0),
        "android": props.get("ro.build.version.release", ""),
        "platform": platform,
        "packages": states,
    }


def package_states(adb: Adb) -> dict:
    """name -> {"enabled": bool, "system": bool}. Two cheap list calls, no per-package dumpsys."""
    def names(*flags):
        out = adb.shell("pm", "list", "packages", *flags)
        return {l.split(":", 1)[1].strip() for l in out.splitlines() if l.startswith("package:")}
    every, disabled, system = names(), names("-d"), names("-s")
    return {n: {"enabled": n not in disabled, "system": n in system} for n in every}


def match_model(db: dict, dev: dict):
    """Exact fingerprint first, then device codename, then the commercial model string."""
    models = db["models"]
    for key in ("fingerprint", "device", "model"):
        value = dev.get(key, "")
        if not value:
            continue
        hits = [m for m in models if m.get(key) and m[key] == value]
        if hits:
            return hits[0], key
    return None, None


def plan(dev: dict, mode: str = "seguro", extra: list[str] | None = None) -> dict:
    """mode: seguro (exact telemetry/ads/demo + generic safe), recomendado (adds generic recommended)."""
    if mode not in ("seguro", "recomendado"):
        raise Error("Modo desconocido: usa seguro o recomendado")
    db = database()
    states = dev["packages"]
    model, matched_by = match_model(db, dev)
    keep = set(model["keep"]) if model else set()
    actions, offered, skipped = [], [], []

    def add(name, reason, source, category):
        if name in (a["name"] for a in actions):
            return
        actions.append({"name": name, "reason": reason, "source": source, "category": category})

    if model:
        for p in model["packages"]:
            name = p["name"]
            if name not in states or not states[name]["enabled"]:
                continue
            info = db["packages"].get(name, {})
            if info.get("tier") in ("protected", "home") or name in keep:
                skipped.append({"name": name, "why": "protegido o parte del inicio"})
            elif p["category"] in DEFAULT_CATEGORIES:
                add(name, p["note"] or p["batch"], f"perfil {model['id']}", p["category"])
            elif mode == "recomendado" and not states[name].get("app") and name not in NEVER_AUTO:
                add(name, p["note"] or p["batch"], f"perfil {model['id']}", p["category"])
            else:
                offered.append({"name": name, "note": p["note"] or p["batch"], "category": p["category"]})
    tiers = {"safe"} | (EXTRA_SAFE if mode == "recomendado" else set())
    for name, st in sorted(states.items()):
        info = db["packages"].get(name)
        if not info or not st["enabled"] or not st["system"] or name in keep:
            continue
        user_facing = st.get("app") or name in NEVER_AUTO
        if info["tier"] in tiers and not (user_facing and info["category"] not in DEFAULT_CATEGORIES):
            add(name, (info["notes"] or [""])[0], f"{info['disabled_in']} modelos", info["category"])
        elif info["tier"] in ("recommended", "safe") and name not in (o["name"] for o in offered):
            offered.append({"name": name, "note": (info["notes"] or [""])[0], "category": info["category"]})
    for name in extra or []:
        package(name)
        info = db["packages"].get(name, {})
        if name not in states:
            raise Error(f"{name} no está instalado")
        if info.get("tier") in ("protected", "home"):
            raise Error(f"{name} está protegido y no se puede deshabilitar con este asistente")
        if states[name]["enabled"]:
            add(name, "elegido por ti", "manual", info.get("category", "optional"))
    offered = [o for o in offered if o["name"] not in {a["name"] for a in actions}]
    return {"model": model["id"] if model else None, "matched_by": matched_by,
            "title": model["title"] if model else None, "mode": mode,
            "actions": actions, "offered": offered, "skipped": skipped}


def health(adb: Adb) -> dict:
    """Quick functional checks after each batch: UI, Home, inputs, network, Play."""
    def ok(*args):
        try:
            adb.shell(*args)
            return True
        except Error:
            return False
    home = ""
    try:
        home = adb.shell("cmd", "package", "resolve-activity", "--brief", "-c", "android.intent.category.HOME",
                         "-a", "android.intent.action.MAIN").splitlines()[-1].strip()
    except Error:
        pass
    procs = adb.shell("ps", "-A", "-o", "NAME")
    return {
        "systemui": "com.android.systemui" in procs,
        "home": home,
        "tv_inputs": ok("dumpsys", "tv_input"),
        "network": "IS_VALIDATED" in adb.shell("dumpsys", "connectivity").split("NetworkOffer")[0],
        "play_services": "com.google.android.gms" in procs or "com.google.android.gms" not in package_states(adb),
    }


def apply(adb: Adb, dev: dict, the_plan: dict, state_dir: Path, log=print) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    backup = state_dir / f"optimizacion-{dev['device'] or 'tv'}-{_now()}.json"
    record = {"schema": 1, "kind": "horizonx-optimization", "created": _now(), "serial": adb.serial,
              "device": {k: dev[k] for k in ("manufacturer", "model", "device", "fingerprint", "sdk")},
              "plan": the_plan, "before": {a["name"]: dev["packages"][a["name"]] for a in the_plan["actions"]},
              "results": {}, "health_before": health(adb)}
    backup.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    for a in the_plan["actions"]:
        name = package(a["name"])
        try:
            out = adb.shell("pm", "disable-user", "--user", "0", name)
            record["results"][name] = "disabled" if "disabled-user" in out else out[:120]
            log(f"  ✓ {name}  ({a['reason'][:60]})")
        except Error as e:
            record["results"][name] = f"error: {str(e)[:160]}"
            log(f"  ✗ {name}: {str(e).splitlines()[0][:100]}")
        backup.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    time.sleep(2)
    record["health_after"] = health(adb)
    backup.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return backup


def restore(adb: Adb, backup: Path, log=print) -> dict:
    record = json.loads(backup.read_text(encoding="utf-8"))
    if record.get("kind") != "horizonx-optimization":
        raise Error("Este archivo no es una copia de optimización de HorizonX")
    done = {}
    for name, before in record["before"].items():
        package(name)
        if not before.get("enabled", True):
            continue  # It was already disabled before HorizonX: leave it as it was.
        try:
            adb.shell("pm", "enable", "--user", "0", name)
            done[name] = "enabled"
            log(f"  ↺ {name}")
        except Error as e:
            done[name] = f"error: {str(e)[:120]}"
            log(f"  ✗ {name}: {str(e).splitlines()[0][:100]}")
    record["restored"] = {"at": _now(), "results": done}
    backup.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return done
