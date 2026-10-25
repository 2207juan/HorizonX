"""Atomic local, authenticated records; locks prevent two concurrent apply/restore runs."""
from __future__ import annotations
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import tempfile
from .adb import Error

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def load_json(path, maximum=32*1024*1024):
    p = Path(path)
    if p.stat().st_size > maximum:
        raise Error("El documento supera el tamaño permitido")
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError) as e:
        raise Error("Documento JSON inválido") from e

def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(prefix=".hx-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(canonical(value) + b"\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

class Store:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        keyfile = self.root / "record.key"
        try:
            fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, "wb") as f:
                f.write(secrets.token_bytes(32)); f.flush(); os.fsync(f.fileno())
        self.key = keyfile.read_bytes()
        if len(self.key) != 32:
            raise Error("Clave local dañada; conserva el respaldo original")

    def path(self, name):
        if not isinstance(name, str) or not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for c in name):
            raise Error("Nombre de registro inválido")
        return self.root / (name + ".json")

    def save(self, name, payload):
        atomic(self.path(name), {"payload": payload, "mac": hmac.new(self.key, canonical(payload), "sha256").hexdigest()})

    def load(self, name):
        value = load_json(self.path(name))
        if not isinstance(value, dict) or "payload" not in value:
            raise Error("Registro sin autenticación local")
        mac = hmac.new(self.key, canonical(value["payload"]), "sha256").hexdigest()
        if not hmac.compare_digest(mac, str(value.get("mac", ""))):
            raise Error("Registro modificado o de otro PC; usa su carpeta de estado original")
        return value["payload"]

    def records(self, prefix="transaction-"):
        return [p.stem for p in sorted(self.root.glob(prefix + "*.json"))]

    @contextmanager
    def lock(self):
        lock = self.root / "operation.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as e:
            raise Error("Hay una operación o bloqueo pendiente. Tras un cierre inesperado, revisa el diario antes de retirar operation.lock manualmente.") from e
        os.write(fd, str(os.getpid()).encode()); os.close(fd)
        try:
            yield
        finally:
            lock.unlink(missing_ok=True)
