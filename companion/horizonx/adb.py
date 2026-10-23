"""Explicit-serial ADB transport. Android help exit 255 is a narrowly validated exception."""
from __future__ import annotations
import re
import shlex
import subprocess

PACKAGE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+\Z")
COMPONENT = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*/[A-Za-z0-9_.$]+\Z")
FAILURE = re.compile(r"SecurityException|Permission Denial|Error:|Failure \[|Exception occurred|Remote exception:|(?m:^\s*(?:Unknown command|Unknown option|Can.t find service):)", re.I)
# Only these exact read-only requests may accept Android's help return value -1 => adb 255.
HELP_HEADERS = {
    ('pm', 'help'): {'Package manager (package) commands:'},
    ('cmd', 'package', 'help'): {'Package manager (package) commands:'},
    ('cmd', 'role', 'help'): {'Role (role) commands:', 'Role manager (role) commands:'},
}

class Error(RuntimeError):
    pass

class CommandError(Error):
    def __init__(self, args, result):
        self.returncode = result.returncode
        self.stdout = result.stdout
        self.stderr = result.stderr
        # Pairing codes never belong in a diagnostic command label.
        label = args[-1] if len(args) >= 2 and args[-2] == 'shell' else ' '.join(str(a) for a in args[:2])
        sections = [f"Comando {label!r} (salida {result.returncode})"]
        if result.stderr.strip():
            sections.append('stderr: ' + result.stderr.strip()[:900])
        if result.stdout.strip():
            sections.append('stdout: ' + result.stdout.strip()[:900])
        super().__init__('\n'.join(sections))

def package(value: str) -> str:
    if not isinstance(value, str) or not PACKAGE.fullmatch(value):
        raise Error("Identificador de paquete inválido")
    return value

def execute(args, timeout=45):
    try:
        return subprocess.run([str(a) for a in args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout, shell=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Error(f"No se pudo ejecutar {args[0]}: {e}") from e

def run(args, timeout=45):
    p = execute(args, timeout)
    # Real operations remain strict, even if the output says Success or contains a help banner.
    if p.returncode or FAILURE.search(p.stdout + '\n' + p.stderr):
        raise CommandError(args, p)
    return p.stdout.strip()

def read_help(args, query, timeout=45):
    if query not in HELP_HEADERS:
        raise Error('La excepción de ayuda no admite esta operación')
    p = execute(args, timeout)
    output = '\n'.join(part.strip() for part in (p.stdout, p.stderr) if part.strip())
    lines = output.splitlines()
    # AOSP BasicShellCommandHandler prints valid help then returns -1; adb shell2 exposes 255.
    # Do not accept exit 1, a killed local process (-1), transport failures or an error + banner.
    invalid = (p.returncode not in (0, 255) or not lines or lines[0].strip() not in HELP_HEADERS[query]
               or FAILURE.search(output)
               or re.search(r'(?im)^\s*(?:adb(?:\.exe)?:|error:|unknown command:|can.t find service:)', output))
    if invalid:
        raise CommandError(args, p)
    return output

def help_commands(text):
    """Read command entries, never a substring mentioned only inside explanatory prose."""
    return set(re.findall(r'^ {0,2}([a-z][a-z0-9-]*)(?=\s|$)', text, re.M))

class Adb:
    def __init__(self, serial: str, executable="adb"):
        if not serial or serial.startswith("-") or any(c.isspace() for c in serial):
            raise Error("Selecciona un serial ADB explícito")
        self.serial, self.executable = serial, str(executable)

    @staticmethod
    def devices(executable="adb"):
        out = run([executable, "devices", "-l"])
        result = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2:
                result.append({"serial": parts[0], "state": parts[1], "description": " ".join(parts[2:])})
        return result

    def command(self, *args, timeout=45):
        return run([self.executable, "-s", self.serial, *args], timeout)

    def shell(self, *args, timeout=45):
        # ADB's remote shell still interprets its command. Quote every argument a second time.
        query = tuple(str(a) for a in args)
        if query in HELP_HEADERS:
            argv = [self.executable, '-s', self.serial, 'shell', shlex.join(query)]
            return read_help(argv, query, timeout)
        return self.command("shell", shlex.join(query), timeout=timeout)

    def optional(self, *args):
        try:
            return {"available": True, "value": self.shell(*args)}
        except Error as e:
            return {"available": False, "error": str(e)}
