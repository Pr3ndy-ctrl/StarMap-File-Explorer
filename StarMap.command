#!/bin/bash
# StarMap File Explorer for macOS. Double-click to start; close this window to stop.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
  exec python3 starmap.py "$@"
fi
echo ""
echo "  StarMap needs Python 3.9 or newer."
echo "  Install it from https://www.python.org/downloads/ (or run: xcode-select --install)"
echo "  then double-click StarMap.command again."
echo ""
read -r -p "  Press Return to close this window. "
