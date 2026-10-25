"""Read-only samples; unsupported metrics are unavailable, never zero-filled."""
from __future__ import annotations
import re
import statistics
from .device import identity, binding, utc
from .adb import Error

def number(pattern, text, cast=float):
    m = re.search(pattern, text, re.M)
    return cast(m[1]) if m else None

def frame_summary(text):
    durations = []
    deadlines = []
    collecting = False
    for line in text.splitlines():
        if line.startswith("Flags,"):
            header = line.strip().rstrip(',').split(",")
            collecting = {'Flags', 'IntendedVsync', 'FrameCompleted'}.issubset(header)
            continue
        if not collecting or not line[:1].isdigit():
            continue
        try:
            values = dict(zip(header, line.split(",")))
            start, end = int(values["IntendedVsync"]), int(values["FrameCompleted"])
            if int(values["Flags"]) == 0 and 0 < end - start < 10_000_000_000:
                durations.append((end - start) / 1_000_000)
                deadline = int(values.get('FrameDeadline', '0'))
                if deadline > start:
                    deadlines.append(end > deadline)
        except (KeyError, ValueError):
            continue
    if not durations:
        return None
    durations.sort()
    return {"count": len(durations), "median_ms": round(statistics.median(durations), 3),
            "p95_ms": round(durations[min(len(durations)-1, int(len(durations)*.95))], 3),
            "over_16_67ms": sum(d > 16.67 for d in durations),
            "over_700ms": sum(d > 700 for d in durations),
            "missed_deadline_frames": sum(deadlines) if deadlines else None,
            "note": "Ventana de frames renderizados; 16,67 ms es referencia de 60 Hz, no FPS ni prueba de jank por sí sola. Puede incluir varias ventanas."}

def measure(adb, condition="unspecified"):
    device = identity(adb)
    commands = {"memory": ("cat", "/proc/meminfo"), "processes": ("ps", "-A"),
                "cpu": ("dumpsys", "cpuinfo"), "launcher_memory": ("dumpsys", "meminfo", "tv.lightos"),
                "frames": ("dumpsys", "gfxinfo", "tv.lightos", "framestats"),
                "uptime": ("cat", "/proc/uptime")}
    samples = {k: adb.optional(*v) for k, v in commands.items()}
    def raw(k):
        return samples[k].get("value", "")
    lines = raw("processes").splitlines()
    metrics = {
        "available_memory_kib": number(r"^MemAvailable:\s*(\d+) kB", raw("memory"), int),
        "total_memory_kib": number(r"^MemTotal:\s*(\d+) kB", raw("memory"), int),
        "process_count": len(lines)-1 if samples["processes"]["available"] and len(lines) > 1 else None,
        "cpu_total_percent": number(r"^\s*([\d.]+)% TOTAL:", raw("cpu")),
        "launcher_pss_kib": number(r"^\s*TOTAL PSS:\s*(\d+)", raw("launcher_memory"), int)
                           or number(r"^\s*TOTAL\s+(\d+)", raw("launcher_memory"), int),
        "launcher_frames": frame_summary(raw("frames")),
        "uptime_seconds": number(r"^([\d.]+)", raw("uptime")),
        "launcher_open_ms": None,
        "remote_input_latency_ms": None,
    }
    return {"schema": 1, "kind": "horizonx-measurement", "created": utc(), "device": device,
            "condition": condition, "metrics": metrics,
            "unavailable": {k: v.get("error", "Sin datos utilizables") for k, v in samples.items() if not v["available"]},
            "notes": ["Muestra puntual, sin detener apps ni reiniciar contadores.",
                      "CPU y frames usan ventanas del sistema que pueden solaparse.",
                      "La latencia real del mando y el arranque en frío requieren una prueba aparte."]}

def compare(before, after):
    if binding(before["device"]) != binding(after["device"]):
        raise Error("Las mediciones pertenecen a otro dispositivo, usuario o firmware")
    if not before.get("condition") or before["condition"] == "unspecified" or before["condition"] != after.get("condition"):
        raise Error("Se necesitan condiciones comparables explícitas e iguales")
    deltas = {}
    for k in ("available_memory_kib", "process_count", "cpu_total_percent", "launcher_pss_kib"):
        a, b = before["metrics"].get(k), after["metrics"].get(k)
        if a is not None and b is not None:
            deltas[k] = {"before": a, "after": b, "delta": round(b-a, 3)}
    return {"kind": "horizonx-comparison", "condition": before["condition"], "deltas": deltas,
            "conclusion": "Diferencias observadas; una pareja de muestras no demuestra mejora ni causalidad.",
            "frames": {"before": before["metrics"].get("launcher_frames"), "after": after["metrics"].get("launcher_frames"),
                       "comparable": False, "reason": "Repite el mismo recorrido en ventanas independientes y revisa las trazas; no se compara automáticamente una ventana acumulada."}}
