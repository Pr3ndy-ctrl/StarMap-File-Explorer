# Development

## Layout

| Path | What it is |
|---|---|
| `starmap.py` | The whole app: scanner, live readouts and the local web server. Standard library only. |
| `web/index.html` | The map page: three.js for the map, plain JavaScript for everything else. |
| `web/vendor/`, `web/fonts/` | three.js r128, Mammoth 1.6.0 and two fonts, bundled so StarMap works offline. |
| `StarMap.command`, `StarMap.bat`, `StarMap.sh` | Launchers for macOS, Windows and Linux. |
| `tools/demo_home.py` | Builds a sample home folder for trying, testing and screenshots. |
| `tests/test_starmap.py` | Unit and server tests. |
| `tests/check_launch.py` | Starts StarMap as a person would and checks it answers. |
| `docs/wiki/` | This wiki. A workflow copies it to the GitHub wiki whenever it changes on `main`. |

## Running from source

```
python3 tools/demo_home.py /tmp/demo-home
STARMAP_HOME=/tmp/demo-home STARMAP_DATA=/tmp/starmap-data STARMAP_OUTSIDE= python3 starmap.py
```

`starmap.py` reads `web/index.html` from disk on every request, so reload the page to see changes to it.

## Tests

```
python3 -m unittest discover -s tests -v
python3 tests/check_launch.py
```

GitHub Actions runs both on macOS, Windows and Linux with Python 3.9 and 3.13 on every push and pull request.

## The scan file

`scan.json` holds:

- `dirs`: one entry per folder, `[name, parent index, kind, file count]`. Index 0 is the home folder. Kind is 0 for a folder, 1 for a nebula (counted, not listed) and 2 for a folder that couldn't be read. A negative count means at least that many; counting stopped early.
- `files`: one entry per file, `[name, folder index, size in bytes, modified time in Unix seconds]`.
- `extra`: everything else, including disk totals (`disk`), nebula sizes in KB (`b`), system-folder parts in KB (`lib`), folders outside home (`outside`), content samples for probable copies (`sig`), parts it couldn't measure (`un`), the platform and the scan time.

## The local API

Everything except the page and its static files needs the session cookie and a `Host` of `127.0.0.1` or `localhost`. POST requests must send JSON and, if they send an `Origin`, it must be StarMap's own.

| Method and path | Purpose |
|---|---|
| `GET /?k=KEY` | Sets the session cookie and redirects to the page. |
| `GET /api/info` | Version, platform, home folder, path separator, system-folder name, whether a scan exists. |
| `GET /api/data` | The saved scan. |
| `POST /api/scan` `{prev}` | Starts a scan. `prev` is the previous item count, used for the progress bar. |
| `GET /api/progress` | Scan state, stage, items read, elapsed time, percentage. |
| `POST /api/stop` | Stops a running scan. |
| `GET /api/system` | Live disk, memory, top apps and network. |
| `GET /file?rel=PATH` | A file for preview, with range support. Paths are relative to the home folder, with `/`. |
| `POST /api/open` `{rel}` | Opens a document in its app. |
| `POST /api/reveal` `{rel}` | Shows a file in Finder, File Explorer or the file manager. |
| `POST /api/trash` `{items: [{rel, keep: [...]}]}` | Moves copies to the Trash after a byte-for-byte check. |

## Contributing

Issues and pull requests are welcome. Please keep StarMap free of dependencies, keep the tests passing on all three systems, and add a test for anything that reads or changes files.
