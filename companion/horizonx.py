#!/usr/bin/env python3
"""Guided installation of the compiled HorizonX APK; Android app source is not included."""
import argparse
import sys
from horizonx import __version__
from horizonx.adb import Error

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version='HorizonX '+__version__)
    parser.parse_args()
    from horizonx.guide import main as guide
    return guide()

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Error, OSError, ValueError, KeyError, TypeError) as e:
        print('HorizonX: '+str(e), file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)
