"""Decide which installed packages are safe to offer for removal.

The rule (from field testing, see README credits): only Samsung-store style
packages (10-char random id + name) are ever candidates. Platform packages
(org.tizen.*, com.samsung.*, and everything else) are never touched, because
removing one can break Home and only a factory reset brings it back.
"""

import re

STORE_PKG = re.compile(r"^[A-Za-z0-9]{10}$")

# Store-pattern packages that are actually TV infrastructure.
PROTECTED_PKGS = {
    "ZODRT12q2l",  # WebAccountExtension (account plumbing)
    "aQjWjLsPaO",  # MultiScreenWebLauncher
    "30IKH0OX8U",  # Aria video background services
    "DclHome001",  # this project's own launcher
}
PROTECTED_NAME_HINTS = ("lowmem", "webaccount", "multiscreen", "adplayer", "launcher")

# Names that are almost never wanted. Everything else store-installed is "optional".
LIKELY_BLOAT_HINTS = (
    "e-manual",
    "emanual",
    "demo",
    "retail",
    "shop",
    "store mode",
    "tips",
    "gaming hub",
    "samsung health",
    "samsung art",
    "ambient",
    "workout",
    "fitness",
    "news",
    "weather",
    "tiktok",
    "facebook watch",
    "pluto",
    "tubi",
    "plex",
    "vudu",
    "fandango",
    "sling",
    "philo",
    "frndly",
    "xumo",
    "freevee",
    "rakuten",
    "amazon music",
    "deezer",
    "pandora",
    "user guide",
    "smartthings",
    "youtube tv",
    "iheart",
    "twitch",
    "steam link",
    "xbox",
    "geforce",
    "utomik",
    "antstream",
    "blacknut",
    "boosteroid",
    "luna",
    "stadia",
)


BLOCK_FIELD = re.compile(r"-{3,}([\w():,]+?)\s*=(.*?)-{5,}\s*$", re.M)


def parse_blocks(text):
    """Newer firmware (Tizen 6+) prints one dashed block of `key =value` per app."""
    apps = []
    for block in re.split(r"\n-{20,}\s*\n", text):
        f = dict((k.strip(), v.strip()) for k, v in BLOCK_FIELD.findall(block))
        if "app_id" not in f:
            continue
        tizen_id = f.get("app_tizen_id") or f["app_id"]
        apps.append(
            {
                "appid": tizen_id,
                "pkgid": f.get("app_package_name") or tizen_id.split(".")[0],
                "name": f.get("app_title") or tizen_id,
                "store_id": f["app_id"],
                "removable": f.get("is_removable") == "1",
                "size_mb": int(f.get("app_size") or 0) // (1024 * 1024),
                "uses": int(f.get("use_count") or 0),
                "version": f.get("app_version") or None,
            }
        )
    return apps


def parse_applist(text):
    """Parse `0 vd_applist` output into [{appid, pkgid, name, ...}].

    Handles the dashed per-app blocks of newer firmware, `key=value` lines and
    tab-separated columns of older firmware, and plain one-id-per-line output.
    """
    if "app_tizen_id" in text:
        return parse_blocks(text)
    apps = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("---", "=", "#")) or line.lower().startswith("total"):
            continue
        fields = dict(re.findall(r"(\w+)\s*[=:]\s*\[?([^\]\t,]+?)\]?(?=\s+\w+\s*[=:]|\s*$|\t|,)", line))
        appid = fields.get("app_tizen_id") or fields.get("appid") or fields.get("app_id") or fields.get("id")
        name = fields.get("app_title") or fields.get("name") or fields.get("title")
        if not appid:
            parts = re.split(r"\t+|\s{2,}", line)
            appid = parts[0]
            name = name or (parts[1] if len(parts) > 1 else None)
        appid = appid.strip()
        if not re.match(r"^[\w.\-]+$", appid):
            continue
        apps.append(
            {
                "appid": appid,
                "pkgid": appid.split(".")[0] if "." in appid else appid,
                "name": (name or appid).strip(),
                "raw": line,
                "version": fields.get("app_version") or None,
            }
        )
    return apps


def classify(app):
    """Return 'protected', 'bloat' or 'optional'."""
    pkgid, name = app["pkgid"], app["name"].lower()
    appid = app["appid"].lower()
    if pkgid in PROTECTED_PKGS:
        return "protected"
    if "removable" in app:
        # Newer firmware says outright what it lets you remove; trust it.
        if not app["removable"]:
            return "protected"
    elif not STORE_PKG.match(pkgid):
        return "protected"
    if any(h in appid or h in name for h in PROTECTED_NAME_HINTS):
        return "protected"
    if any(h in name for h in LIKELY_BLOAT_HINTS):
        return "bloat"
    return "optional"
