#!/usr/bin/env sh
# Linux/macOS. No command is executed against a device unless explicitly requested.
exec python3 "$(dirname "$0")/horizonx.py" "$@"
