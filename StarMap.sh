#!/bin/sh
# StarMap File Explorer for Linux. Run ./StarMap.sh; press Ctrl+C to stop.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  exec python3 starmap.py "$@"
fi
echo "StarMap needs Python 3.9 or newer. Install python3 with your package manager, then run this again."
exit 1
