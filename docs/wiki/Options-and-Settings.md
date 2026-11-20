# Options and settings

## Command-line options

```
python3 starmap.py [--port PORT] [--no-browser] [--version]
```

| Option | Effect |
|---|---|
| `--port 8123` | Use that port on 127.0.0.1. By default StarMap uses 47615, or the next free one. |
| `--no-browser` | Don't open the browser. Open the address StarMap prints yourself. |
| `--version` | Show the version and stop. |

The launchers pass options through, for example `./StarMap.sh --no-browser`.

## Environment variables

| Variable | Effect |
|---|---|
| `STARMAP_HOME` | Map this folder instead of your home folder. |
| `STARMAP_DATA` | Keep the saved scan in this folder. |
| `STARMAP_OUTSIDE` | Folders outside the home folder to measure, separated by `:` (`;` on Windows). Set it empty to skip them, which makes scans faster. |

macOS and Linux:

```
STARMAP_HOME=~/Projects STARMAP_OUTSIDE= python3 starmap.py
```

Windows (PowerShell):

```
$env:STARMAP_HOME = "$HOME\Projects"; $env:STARMAP_OUTSIDE = ""; py starmap.py
```

## Starting afresh

Delete StarMap's data folder (see [Privacy and security](Privacy-and-Security)) and start StarMap again; it runs a fresh first scan.

## Limits

- Home folders with more than 250,000 files are mapped in full up to that point; further folders are drawn as nebulae so the map stays quick.
- Measuring the system folder stops after 8 minutes and folders outside the home folder after 4 minutes. Anything unfinished is reported as too large to measure.
