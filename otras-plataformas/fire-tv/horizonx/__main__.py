from __future__ import annotations
import argparse
import getpass
import json
from pathlib import Path
import re
import shlex
import sys
import secrets
from .adb import Adb, Error, run
from .device import inventory, utc
from .profiles import Database, analyze, ROOT
from .store import Store, atomic
from . import transactions as tx, metrics, dns, installer, startup, home, interface, volume, profile


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))

def receipt(value):
    # Information only; never a source of commands or authorization in the APK.
    if value.get('kind','').startswith('horizonx-volume-'):
        raise Error('El puente de volumen se recupera con volume-restore; no es un informe de paquetes para importar.')
    if value.get('kind','').startswith('horizonx-profile-'):
        raise Error('La sincronización de identidad es privada; usa profile-recover para recuperar el estado nativo.')
    if value.get('kind') in ('horizonx-interface-plan','horizonx-interface-transaction'):
        raise Error('Los ajustes de interfaz se revisan con show y se recuperan con interface-restore; no son un informe de paquetes para importar en la TV.')
    device = value.get("device", {})
    changes = []
    for action in value.get("actions", []):
        changes.append({"name": action["name"], "previous": action["before"]["enabled"],
                        "current": action["after_enabled"] if action.get("status") == "applied" else None,
                        "status": action.get("status", "prepared")})
    return {"schema": 1, "kind": "horizonx-maintenance-report", "created": utc(),
            "device": {k: device.get(k) for k in ("manufacturer", "model", "fingerprint", "sdk", "user")},
            "status": value.get("status", "analysis-only"), "changes": changes,
            "profile": value.get("analysis", {}).get("profile"),
            "profile_status": value.get("analysis", {}).get("profile_status", "analysis-only"),
            "note": "Informe informativo del PC; no acredita el estado actual ni concede permisos."}

def parser():
    p = argparse.ArgumentParser(description="HorizonX · asistente local Android TV. Sin operaciones al abrir.")
    p.add_argument("--adb", default="adb", help="Ruta de Android Platform Tools")
    p.add_argument("--serial", help="Serial concreto de adb devices; nunca se selecciona automáticamente")
    p.add_argument("--state", default=str(Path.home()/".horizonx"), help="Carpeta privada de diarios y clave local")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("devices", help="Lista dispositivos autorizados o pendientes")
    sub.add_parser("discover", help="Descubrimiento mDNS ADB, sin escanear puertos")
    for name in ("connect", "pair"):
        q = sub.add_parser(name); q.add_argument("endpoint")
    q = sub.add_parser("scan", help="Inventario de solo lectura")
    q.add_argument("--mode", choices=("conservative", "balanced", "custom"), default="conservative")
    q.add_argument("--output", help="Informe público JSON, sin clave local")
    q.add_argument("--references", action="store_true", help="Añade coincidencias externas informativas")
    q = sub.add_parser("plan"); q.add_argument("scan_id"); q.add_argument("--select", nargs="+", required=True)
    q.add_argument("--mode", choices=("conservative", "balanced", "custom"), default="conservative")
    for name in ("apply", "restore", "dns-apply", "dns-restore", "interface-apply", "interface-restore", "volume-activate", "volume-restore", "profile-sync", "profile-recover"):
        q = sub.add_parser(name); q.add_argument("record_id"); q.add_argument("--approve", required=True)
    q = sub.add_parser("show"); q.add_argument("record_id")
    sub.add_parser("records")
    q = sub.add_parser("recovery", help="Muestra inversas sin conectar; no ejecuta comandos"); q.add_argument("record_id")
    q = sub.add_parser("export"); q.add_argument("record_id"); q.add_argument("output")
    q = sub.add_parser("measure"); q.add_argument("--condition", required=True)
    q = sub.add_parser("compare"); q.add_argument("before_id"); q.add_argument("after_id")
    sub.add_parser("home-status", help="Consulta el Home actual sin modificarlo")
    sub.add_parser("home-plan", help="Respalda y prepara seleccionar HorizonX; no cambia Inicio")
    for name in ("home-activate", "home-restore"):
        q = sub.add_parser(name); q.add_argument("record_id"); q.add_argument("--approve", required=True)
    q = sub.add_parser("home-recovery", help="Muestra inversas Home sin conectar"); q.add_argument("record_id")
    sub.add_parser("startup-plan", help="Prepara una prueba que abre el launcher; aún no lo abre")
    q = sub.add_parser("startup"); q.add_argument("record_id"); q.add_argument("--approve", required=True)
    q = sub.add_parser("dns-plan"); q.add_argument("hostname")
    q = sub.add_parser("interface-plan", help="Prepara sonidos de Android y transiciones, sin cambios")
    q.add_argument("--quiet-system", action="store_true"); q.add_argument("--faster-transitions", action="store_true")
    sub.add_parser("volume-plan",help="Prepara el indicador de volumen Android 14; sin cambios")
    q=sub.add_parser("volume-status",help="Consulta una sesión de burbuja");q.add_argument("record_id")
    q=sub.add_parser("profile-plan",help="Prepara la copia privada del perfil nativo Google TV, sin cambios");q.add_argument("--account-hash")
    q = sub.add_parser("install-plan"); q.add_argument("apk"); q.add_argument("--apksigner", required=True); q.add_argument("--aapt2", required=True)
    q = sub.add_parser("install"); q.add_argument("record_id"); q.add_argument("--approve", required=True); q.add_argument("--apksigner", required=True); q.add_argument("--aapt2", required=True)
    sub.add_parser("compatibility", help="Estado de perfiles y familias reconocidas, sin ADB")
    return p

def main(argv=None):
    args = parser().parse_args(argv)
    db = Database()
    if args.command == "compatibility":
        emit(db.data); return 0
    if args.command == "devices":
        emit(Adb.devices(args.adb)); return 0
    if args.command == "discover":
        print(run([args.adb, "mdns", "services"])); return 0
    if args.command in ("connect", "pair"):
        if not re.fullmatch(r"(?:[A-Za-z0-9.-]+|\[[A-Fa-f0-9:]+\]):[0-9]{1,5}", args.endpoint) or not 0 < int(args.endpoint.rsplit(":", 1)[1]) < 65536:
            raise Error("Indica host:puerto mostrado por el televisor")
        if args.command == "pair":
            code = getpass.getpass("Código de emparejamiento (no se guardará): ")
            if not re.fullmatch(r"\d{6}", code):
                raise Error("Código inválido")
            print(run([args.adb, "pair", args.endpoint, code]))
        else:
            print(run([args.adb, "connect", args.endpoint]))
        return 0
    store = Store(args.state)
    if args.command == "records":
        emit([{ "id": n, "kind": (v := store.load(n)).get("kind"), "status": v.get("status"), "created": v.get("created")}
              for n in store.records("")]); return 0
    if args.command == "show":
        value = store.load(args.record_id)
        result = {"record": value}
        actions = {"horizonx-plan": "APLICAR", "horizonx-transaction": "RESTAURAR",
                   "horizonx-dns-plan": "DNS-EXPERIMENTAL", "horizonx-dns-transaction": "RESTAURAR-DNS", "horizonx-install-plan": "INSTALAR", "horizonx-startup-plan": "ABRIR-PARA-MEDIR", "horizonx-home-plan": "ACTIVAR-INICIO", "horizonx-home-transaction": "RESTAURAR-INICIO", "horizonx-interface-plan": "APLICAR-INTERFAZ", "horizonx-interface-transaction": "RESTAURAR-INTERFAZ"}
        actions.update({'horizonx-volume-plan':'ACTIVAR-BURBUJA','horizonx-volume-transaction':'RESTAURAR-BURBUJA'})
        actions.update({'horizonx-profile-plan':'SINCRONIZAR-PERFIL','horizonx-profile-transaction':'RECUPERAR-PERFIL-NATIVO'})
        if value.get("kind") in actions:
            result["approval_token"] = tx.token(actions[value["kind"]], value)
        emit(result); return 0
    if args.command == "export":
        atomic(args.output, receipt(store.load(args.record_id))); print(args.output); return 0
    if args.command == "home-recovery":
        value = store.load(args.record_id)
        emit({"device": value["device"], "commands": [shlex.join(c) for c in home.inverse(value)],
              "note": "Solo revisión, no se ejecuta. Comprueba identidad, firmware y conflictos. Prefiere home-restore con validación."})
        return 0
    if args.command == "recovery":
        value = store.load(args.record_id)
        if value.get('kind','').startswith('horizonx-volume-'):
            raise Error('Usa volume-restore con el registro y su aprobación para devolver primero el controlador original; no basta con quitar permisos.')
        if value.get('kind','').startswith('horizonx-profile-'):
            raise Error('Usa profile-recover para comprobar la identidad y restaurar el estado del selector nativo.')
        if value.get("kind") == "horizonx-interface-transaction":
            commands = interface.inverse(value)
        elif value.get("kind") == "horizonx-dns-transaction":
            commands = [["settings", "delete" if value["before"][k] is None else "put", "global", k] + ([] if value["before"][k] is None else [value["before"][k]]) for k in reversed(dns.KEYS) if k in value["attempted"]]
        else:
            commands = tx.recovery_commands(value)
        emit({"device": value["device"], "instructions": "Comprueba dispositivo, firmware, versión y conflictos antes de ejecutar. Preferir restore con validación. Home nunca fue modificado por el optimizador.",
              "adb_serial": "SELECCIONAR_SERIAL_ACTUAL", "remote_commands": [shlex.join(c) for c in commands]}); return 0
    if args.command == "compare":
        emit(metrics.compare(store.load(args.before_id), store.load(args.after_id))); return 0
    if not args.serial:
        raise Error("Falta --serial. Consulta devices y elige el televisor explícitamente.")
    adb = Adb(args.serial, args.adb)
    if args.command == "home-status":
        emit(home.status(adb))
    elif args.command == "home-plan":
        value = home.prepare(adb, store); emit({"record": value, "approval_token": tx.token("ACTIVAR-INICIO", value)})
    elif args.command == "home-activate":
        value = home.activate(adb, store, args.record_id, args.approve); emit(value)
        return 0 if value["status"] == "activated" else 2
    elif args.command == "home-restore":
        value = home.restore(adb, store, args.record_id, args.approve); emit(value)
        return 0 if value["status"] == "restored" else 2
    elif args.command == "interface-plan":
        value=interface.plan(adb,store,args.quiet_system,args.faster_transitions); emit({"record":value,"approval_token":tx.token("APLICAR-INTERFAZ",value)})
    elif args.command == 'volume-plan':
        value=volume.plan(adb,store);emit({'record':value,'approval_token':tx.token('ACTIVAR-BURBUJA',value)})
    elif args.command == 'volume-activate':
        value=volume.activate(adb,store,args.record_id,args.approve);emit(value);return 0 if value['status']=='active' else 2
    elif args.command == 'volume-restore':
        value=volume.restore(adb,store,args.record_id,args.approve);emit(value);return 0 if value['status']=='restored' else 2
    elif args.command == 'volume-status':
        emit(volume.status(adb,store.load(args.record_id)))
    elif args.command == 'profile-plan':
        value=profile.plan(adb,store,args.account_hash);emit({'record':value,'approval_token':tx.token('SINCRONIZAR-PERFIL',value)})
    elif args.command == 'profile-sync':
        value=profile.sync(adb,store,args.record_id,args.approve);emit(value);return 0 if value['status']=='synced' else 2
    elif args.command == 'profile-recover':
        value=profile.restore_native(adb,store,args.record_id,args.approve);emit(value);return 0 if value['status'] in ('synced','restored') else 2
    elif args.command == "interface-apply":
        value=interface.apply(adb,store,args.record_id,args.approve);emit(value);return 0 if value["status"]=="applied" else 2
    elif args.command == "interface-restore":
        value=interface.restore(adb,store,args.record_id,args.approve);emit(value);return 0 if value["status"]=="restored" else 2
    elif args.command == "scan":
        value = inventory(adb)
        value["analysis"] = analyze(value, db, args.mode)
        if args.references:
            value["external_references"] = db.references(value["device"], value["packages"])
        value["id"] = "scan-" + secrets.token_hex(8)
        store.save(value["id"], value)
        if args.output:
            atomic(args.output, value)
        emit({"id": value["id"], "device": value["device"], "analysis": value["analysis"],
              "unreadable": value["unreadable"], "home": value["home"]})
    elif args.command == "plan":
        value = tx.create_plan(adb, store, store.load(args.scan_id), db, args.select, args.mode)
        emit({"record": value, "approval_token": tx.token("APLICAR", value)})
    elif args.command == "apply":
        value = tx.apply(adb, store, db, args.record_id, args.approve, metrics.measure); emit(value)
        return 0 if value["status"] == "applied" else 2
    elif args.command == "restore":
        value = tx.restore(adb, store, args.record_id, args.approve); emit(value)
        return 0 if value["status"] == "restored" else 2
    elif args.command == "measure":
        value = metrics.measure(adb, args.condition); value["id"] = "measurement-" + secrets.token_hex(8)
        store.save(value["id"], value); emit(value)
    elif args.command == "startup-plan":
        value = startup.plan(adb, store); emit({"record": value, "approval_token": tx.token("ABRIR-PARA-MEDIR", value)})
    elif args.command == "startup":
        value = startup.measure(adb, store, args.record_id, args.approve); emit(value)
        return 0 if value["status"] == "measured" else 2
    elif args.command == "dns-plan":
        value = dns.plan(adb, store, db, args.hostname); emit({"record": value, "approval_token": tx.token("DNS-EXPERIMENTAL", value)})
    elif args.command == "dns-apply":
        value = dns.apply(adb, store, db, args.record_id, args.approve); emit(value)
        return 0 if value["status"] == "applied" else 2
    elif args.command == "dns-restore":
        value = dns.restore(adb, store, args.record_id, args.approve); emit(value)
        return 0 if value["status"] == "restored" else 2
    elif args.command == "install-plan":
        value = installer.plan(adb, store, args.apk, args.apksigner, args.aapt2); emit({"record": value, "approval_token": tx.token("INSTALAR", value)})
    elif args.command == "install":
        value = installer.install(adb, store, args.record_id, args.approve, args.apksigner, args.aapt2); emit(value)
        return 0 if value["status"] == "installed" else 2
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Error, OSError, ValueError, KeyError, TypeError) as e:
        print(f"HorizonX: {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("Interrumpido. Conserva la carpeta de estado; revisa records antes de repetir.", file=sys.stderr)
        sys.exit(130)
