#!/usr/bin/env python3
"""
StarMap File Explorer
=====================

Draws every file in your home folder as a star in a 3D map, shows where the
disk space goes, and keeps live disk, memory and network readouts on screen.

Run it with:  python3 starmap.py        (Windows: py starmap.py)

It needs only Python 3.9 or newer: no packages to install. Everything stays on
this computer. The map is served to your browser from 127.0.0.1 (this computer
only) and every request has to carry a key that is created fresh each time
StarMap starts.

StarMap only reads, with two exceptions that happen when you press a button:
"Open file" / "Show in Finder" ask the system to open a file, and "Move to
Trash" moves copies you ticked to the Trash or Recycle Bin after checking,
byte for byte, that an identical copy is being kept.
"""

import argparse
import collections
import hashlib
import json
import mimetypes
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP = "StarMap File Explorer"
VERSION = "1.0.0"
DEFAULT_PORT = 47615

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "web")
HOME = os.path.abspath(os.environ.get("STARMAP_HOME") or os.path.expanduser("~"))
PLATFORM = "darwin" if sys.platform == "darwin" else "win32" if os.name == "nt" else "linux"

# The folder the operating system keeps app data in, inside the home folder.
SYS_DIR = {"darwin": "Library", "win32": "AppData"}.get(PLATFORM)

# Folders that are drawn as one cloud (a "nebula") instead of one star per file.
COLLAPSE = set(
    "node_modules .git .hg .svn .npm .gem .cache .trae .codex .npm-global Pods .next .nuxt venv .venv env "
    "__pycache__ DerivedData .gradle .m2 .cargo .rustup .expo .pm2 .zsh_sessions .cocoapods .swiftpm .local "
    ".fontconfig site-packages .turbo .dart_tool .pub-cache .idea .vscode .vscode-server vendor bower_components "
    ".pnpm-store .yarn .Trash .ssh .gnupg .aws .docker .claude .kube .android .nuget .conda anaconda3 miniconda3 "
    "$RECYCLE.BIN".split()
)
if SYS_DIR:
    COLLAPSE.add(SYS_DIR)
COLLAPSE_EXT = tuple(
    ".app .photoslibrary .framework .xcodeproj .xcworkspace .bundle .musiclibrary .tvlibrary .imovielibrary "
    ".fcpbundle .logicx .band .xcassets .lproj .plugin .kext .vst .vst3 .component".split()
)
SKIP_FILES = {".DS_Store", ".localized", "desktop.ini", "Thumbs.db", "NTUSER.DAT", "ntuser.dat.LOG1", "ntuser.dat.LOG2"}

# Past this many stars, further folders are drawn as nebulae so the map stays fast.
MAX_STARS = 250_000

# File types the page can preview, and the type each is served as.
PREVIEW_TYPES = {}
for _x in "mp3:audio/mpeg wav:audio/wav m4a:audio/mp4 aac:audio/aac ogg:audio/ogg opus:audio/ogg flac:audio/flac aiff:audio/aiff aif:audio/aiff".split():
    _e, _t = _x.split(":"); PREVIEW_TYPES[_e] = _t
for _x in "mp4:video/mp4 m4v:video/mp4 mov:video/quicktime webm:video/webm".split():
    _e, _t = _x.split(":"); PREVIEW_TYPES[_e] = _t
for _x in "png:image/png jpg:image/jpeg jpeg:image/jpeg webp:image/webp gif:image/gif svg:image/svg+xml ico:image/x-icon bmp:image/bmp".split():
    _e, _t = _x.split(":"); PREVIEW_TYPES[_e] = _t
PREVIEW_TYPES["pdf"] = "application/pdf"
PREVIEW_TYPES["docx"] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
for _e in ("md txt json csv xml yaml yml log sql conf sh bat ps1 html htm css js ts tsx jsx cjs mjs py php rb go rs "
           "java c h cpp cs swift kt vue scss toml ini plist strings service example out gitignore").split():
    PREVIEW_TYPES[_e] = "text/plain; charset=utf-8"

# Never launched by "Open file": these would run code instead of opening a document.
NO_OPEN = tuple(
    (".app .command .sh .bash .zsh .csh .pkg .mpkg .dmg .terminal .workflow .scpt .applescript .tool .action "
     ".jar .py .pyw .rb .pl .php .exe .com .bat .cmd .msi .msp .ps1 .psm1 .vbs .vbe .js .jse .wsf .wsh .hta "
     ".lnk .url .scr .cpl .msc .reg .pif .gadget .inf .desktop .run .appimage .deb .rpm").split()
)


def data_dir():
    """Where StarMap keeps its last scan."""
    if os.environ.get("STARMAP_DATA"):
        d = os.environ["STARMAP_DATA"]
    elif PLATFORM == "darwin":
        d = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "StarMap")
    elif PLATFORM == "win32":
        d = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "StarMap")
    else:
        d = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share"), "starmap")
    os.makedirs(d, exist_ok=True)
    return d


def scan_file():
    return os.path.join(data_dir(), "scan.json")


def run_out(cmd, timeout=6):
    try:
        kw = {}
        if PLATFORM == "win32":
            kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace", **kw).stdout
    except Exception:
        return ""


# ---------------------------------------------------------------- scanning

def is_link(entry):
    """True for symlinks, and for Windows junctions and other reparse points, which can loop."""
    try:
        if entry.is_symlink():
            return True
        if PLATFORM == "win32":
            attrs = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
            return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
    except OSError:
        return True
    return False


def is_cloud_only(st):
    """True when the file's contents live in the cloud, so reading it would download it."""
    if PLATFORM == "darwin":
        return bool(getattr(st, "st_flags", 0) & 0x40000000)  # SF_DATALESS
    if PLATFORM == "win32":
        return bool(getattr(st, "st_file_attributes", 0) & (0x1000 | 0x40000 | 0x400000))  # OFFLINE, RECALL_ON_OPEN, RECALL_ON_DATA_ACCESS
    return False


def collapsed(name):
    return name in COLLAPSE or name.lower().endswith(COLLAPSE_EXT)


class Stop(Exception):
    pass


# Deep folder trees are walked recursively; give the scan room.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))
try:
    threading.stack_size(64 * 1024 * 1024)
except (ValueError, RuntimeError):
    pass


S = {"state": "idle", "seen": 0, "where": "", "t0": 0.0, "prev": 0, "error": "", "stage": ""}
LOCK = threading.Lock()


def tick(n, where):
    S["seen"] += n
    S["where"] = where
    if S["state"] == "stopping":
        raise Stop()


def disk_bytes(st):
    blocks = getattr(st, "st_blocks", None)
    return blocks * 512 if blocks is not None else st.st_size


def measure(path, deadline=None):
    """Count files and bytes on disk under a folder. Returns (files, bytes, complete)."""
    n = b = 0
    stack = [path]
    while stack:
        if deadline and time.time() > deadline:
            return n, b, False
        p = stack.pop()
        try:
            with os.scandir(p) as it:
                k = 0
                for e in it:
                    k += 1
                    try:
                        if is_link(e):
                            continue
                        if e.is_dir(follow_symlinks=False):
                            stack.append(e.path)
                        else:
                            n += 1
                            b += disk_bytes(e.stat(follow_symlinks=False))
                    except OSError:
                        pass
                tick(k, p)
        except OSError:
            pass
    return n, b, True


def rel(p):
    return "~" + p[len(HOME):].replace(os.sep, "/")


def scan():
    dirs = []   # [name, parent index, kind (0 folder, 1 nebula, 2 unreadable), file count for nebulae]
    files = []  # [name, folder index, size, modified]
    bkb = {}
    denied = [0]
    sys_idx = [-1]

    def nebula(e, idx):
        n, b, done = measure(e.path, time.time() + 180)
        dirs.append([e.name, idx, 1, n if done else -max(n, 1)])
        if b > 0:
            bkb[str(len(dirs) - 1)] = int(b / 1024)

    def walk(path, parent, name):
        idx = len(dirs)
        dirs.append([name, parent, 0, 0])
        try:
            with os.scandir(path) as it:
                ents = sorted(it, key=lambda e: e.name)
        except OSError:
            denied[0] += 1
            dirs[idx][2] = 2
            return
        tick(len(ents), rel(path))
        for e in ents:
            try:
                if is_link(e):
                    continue
                if e.is_dir(follow_symlinks=False):
                    if parent == -1 and e.name == SYS_DIR:
                        dirs.append([e.name, idx, 1, 0])
                        sys_idx[0] = len(dirs) - 1
                    elif collapsed(e.name) or len(files) >= MAX_STARS:
                        nebula(e, idx)
                    else:
                        walk(e.path, idx, e.name)
                else:
                    if e.name in SKIP_FILES:
                        continue
                    st = e.stat(follow_symlinks=False)
                    files.append([e.name, idx, st.st_size, int(st.st_mtime)])
            except OSError:
                denied[0] += 1

    S["stage"] = "Reading folders"
    walk(HOME, -1, "~")

    # The system folder (Library on a Mac, AppData on Windows), measured piece by piece.
    lib, un = [], []
    lib_files = 0
    lib_complete = True
    if SYS_DIR and os.path.isdir(os.path.join(HOME, SYS_DIR)):
        S["stage"] = "Measuring " + SYS_DIR
        root = os.path.join(HOME, SYS_DIR)
        end = time.time() + 8 * 60

        def piece(relp):
            nonlocal lib_files, lib_complete
            full = os.path.join(root, *relp.split("/"))
            try:
                os.scandir(full).close()
            except OSError:
                un.append([SYS_DIR + "/" + relp, "blocked"]); lib_complete = False; return
            if time.time() > end:
                un.append([SYS_DIR + "/" + relp, "too large to measure"]); lib_complete = False; return
            n, b, done = measure(full, end)
            lib_files += n
            if done:
                lib.append([SYS_DIR + "/" + relp, int(b / 1024)])
            else:
                un.append([SYS_DIR + "/" + relp, "too large to measure"]); lib_complete = False

        def children(relp):
            full = os.path.join(root, *relp.split("/")) if relp else root
            try:
                with os.scandir(full) as it:
                    return sorted(e.name for e in it if e.is_dir(follow_symlinks=False) and not is_link(e))
            except OSError:
                return None

        if PLATFORM == "darwin":
            split = ("Application Support", "Containers", "Caches", "Developer", "Group Containers")
            deeper = {"Developer": ("Xcode", "CoreSimulator")}
        else:
            split = ("Local", "Roaming", "LocalLow")
            deeper = {}
        for t in children("") or []:
            if t in split:
                subs = children(t)
                if subs is None:
                    un.append([SYS_DIR + "/" + t, "blocked"]); lib_complete = False; continue
                for s2 in subs:
                    p2 = t + "/" + s2
                    if s2 in deeper.get(t, ()):
                        for s3 in children(p2) or []:
                            piece(p2 + "/" + s3)
                    else:
                        piece(p2)
            else:
                piece(t)
        if sys_idx[0] >= 0:
            dirs[sys_idx[0]][3] = lib_files if lib_complete else -max(lib_files, 1)
        lib.sort(key=lambda x: -x[1])

    # Named parts that the recommendations need exactly.
    parts = {}
    for p in (".npm/_cacache", ".cache/pip", ".cache/yarn"):
        full = os.path.join(HOME, *p.split("/"))
        if os.path.isdir(full):
            n, b, done = measure(full, time.time() + 120)
            if done:
                parts["~/" + p] = int(b / 1024)

    # The main folders outside the home folder, as far as this account may read them.
    S["stage"] = "Measuring folders outside the home folder"
    outside = []
    snapshots = None
    if os.environ.get("STARMAP_OUTSIDE") is not None:
        cands = [c for c in os.environ["STARMAP_OUTSIDE"].split(os.pathsep) if c]
    elif PLATFORM == "darwin":
        cands = ["/Applications", "/Library", "/Users/Shared", "/opt", "/usr/local", "/private/var/vm",
                 "/private/var/folders", "/private/var/db", "/private/tmp"]
    elif PLATFORM == "win32":
        drive = os.path.splitdrive(HOME)[0] or "C:"
        cands = [drive + "\\" + n for n in ("Program Files", "Program Files (x86)", "ProgramData", "Windows")]
    else:
        cands = ["/usr", "/opt", "/var", "/snap", "/srv"]
    if os.environ.get("STARMAP_OUTSIDE") is None and PLATFORM in ("darwin", "linux"):
        base = os.path.dirname(HOME)
        try:
            for e in os.scandir(base):
                if e.is_dir(follow_symlinks=False) and e.name not in ("Shared",) and os.path.realpath(e.path) != os.path.realpath(HOME):
                    cands.append(e.path)
        except OSError:
            pass
    oend = time.time() + 4 * 60
    for p in cands:
        if not os.path.isdir(p):
            continue
        n, b, done = measure(p, oend)
        if b > 0:
            outside.append([p, int(b / 1024), bool(done)])
    if PLATFORM == "win32" and os.environ.get("STARMAP_OUTSIDE") is None:
        # Page, swap and hibernation files sit at the root of the drive.
        drive = (os.path.splitdrive(HOME)[0] or "C:") + "\\"
        try:
            with os.scandir(drive) as it:
                for e in it:
                    try:
                        if e.is_file(follow_symlinks=False) and e.stat().st_size > 5e8:
                            outside.append([e.path, int(e.stat().st_size / 1024), True])
                    except OSError:
                        pass
        except OSError:
            pass
    outside.sort(key=lambda x: -x[1])
    if PLATFORM == "darwin":
        out = run_out(["tmutil", "listlocalsnapshots", "/"], timeout=8)
        snapshots = sum(1 for ln in out.splitlines() if "com.apple" in ln)

    # Probable copies: same name and size, then matching samples of the contents.
    S["stage"] = "Comparing probable copies"

    def path_of(d):
        a = []
        while d > 0:
            a.append(dirs[d][0]); d = dirs[d][1]
        return os.path.join(HOME, *reversed(a))

    groups = collections.defaultdict(list)
    for i, f in enumerate(files):
        if f[2] > 1024:
            groups[(f[0], f[2])].append(i)
    sig = {}
    for v in groups.values():
        if len(v) < 2:
            continue
        for i in v:
            p = os.path.join(path_of(files[i][1]), files[i][0])
            try:
                st = os.stat(p)
                if is_cloud_only(st):
                    sig[str(i)] = "cloud%d" % i  # never download a file just to compare it
                    continue
                h = hashlib.sha1()
                with open(p, "rb") as fh:
                    h.update(fh.read(65536))
                    if files[i][2] > 131072:
                        fh.seek(-65536, 2); h.update(fh.read(65536))
                sig[str(i)] = h.hexdigest()[:12]
            except OSError:
                sig[str(i)] = "x%d" % i
            tick(1, "comparing " + files[i][0])

    du = shutil.disk_usage(HOME)
    at = int(time.time())
    extra = {"sig": sig, "b": bkb, "lib": [x for x in lib if x[1] >= 50000], "libTotalKb": sum(x[1] for x in lib),
             "un": un, "disk": {"totalGb": round(du.total / 1e9, 1), "usedGb": round(du.used / 1e9, 1), "freeGb": round(du.free / 1e9, 1)},
             "parts": parts, "outside": outside, "snapshots": snapshots, "scannedAt": at, "source": "app",
             "platform": PLATFORM, "sysDir": SYS_DIR, "denied": denied[0], "capped": len(files) >= MAX_STARS}
    return {"at": at, "dirs": dirs, "files": files, "extra": extra}


def run_scan():
    try:
        pack = scan()
        path = scan_file()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(pack, fh, separators=(",", ":"), ensure_ascii=False)
        os.replace(tmp, path)
        S["state"] = "done"
    except Stop:
        S["state"] = "idle"; S["error"] = "stopped"
    except Exception as e:  # report it to the page, never crash the app
        S["state"] = "error"; S["error"] = "%s: %s" % (type(e).__name__, e)


# ---------------------------------------------------------------- live readouts

def memory_now():
    try:
        import psutil  # optional; used when installed
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        wired = getattr(vm, "wired", 0) or 0
        cached = (getattr(vm, "cached", 0) or 0) + (getattr(vm, "buffers", 0) or 0)
        app = max(0, vm.total - vm.available - wired)
        return {"total": vm.total, "app": app, "wired": wired, "compressed": 0, "cached": min(cached, vm.available),
                "free": max(0, vm.available - min(cached, vm.available)), "swapUsed": sw.used}
    except Exception:
        pass
    if PLATFORM == "darwin":
        try:
            total = int(run_out(["sysctl", "-n", "hw.memsize"]).strip())
            ps_ = 4096
            v = {}
            for ln in run_out(["vm_stat"]).splitlines():
                if "page size of" in ln:
                    ps_ = int(ln.split("page size of")[1].split()[0])
                elif ":" in ln:
                    k, x = ln.split(":", 1)
                    try:
                        v[k.strip().strip('"')] = int(x.strip().rstrip("."))
                    except ValueError:
                        pass
            wired = v.get("Pages wired down", 0) * ps_
            comp = v.get("Pages occupied by compressor", 0) * ps_
            purge = v.get("Pages purgeable", 0)
            app = max(0, v.get("Anonymous pages", 0) - purge) * ps_
            cached = (v.get("File-backed pages", 0) + purge) * ps_
            free = max(0, total - wired - comp - app - cached)
            swap = 0.0
            sw = run_out(["sysctl", "-n", "vm.swapusage"])
            if "used =" in sw:
                x = sw.split("used =")[1].split()[0]
                mult = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}.get(x[-1].upper(), 1)
                swap = float(x[:-1]) * mult if x[-1].isalpha() else float(x)
            return {"total": total, "app": app, "wired": wired, "compressed": comp, "cached": cached, "free": free, "swapUsed": swap}
        except Exception:
            return None
    if PLATFORM == "win32":
        try:
            import ctypes

            class MEMSTAT(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEMSTAT()
            m.dwLength = ctypes.sizeof(MEMSTAT)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                return None
            used = m.ullTotalPhys - m.ullAvailPhys
            return {"total": m.ullTotalPhys, "app": used, "wired": 0, "compressed": 0, "cached": 0,
                    "free": m.ullAvailPhys, "swapUsed": None}
        except Exception:
            return None
    try:
        m = {}
        with open("/proc/meminfo") as fh:
            for ln in fh:
                k, x = ln.split(":", 1)
                m[k] = int(x.split()[0]) * 1024
        cached = m.get("Cached", 0) + m.get("Buffers", 0) + m.get("SReclaimable", 0)
        avail = m.get("MemAvailable", m.get("MemFree", 0) + cached)
        return {"total": m["MemTotal"], "app": max(0, m["MemTotal"] - avail), "wired": 0, "compressed": 0,
                "cached": min(cached, avail), "free": max(0, avail - cached),
                "swapUsed": m.get("SwapTotal", 0) - m.get("SwapFree", 0)}
    except Exception:
        return None


def top_apps():
    apps = collections.Counter()
    try:
        import psutil
        for p in psutil.process_iter(["name", "memory_info"]):
            try:
                apps[p.info["name"] or "?"] += p.info["memory_info"].rss
            except Exception:
                pass
        return apps.most_common(10)
    except Exception:
        pass
    if PLATFORM == "win32":
        import csv
        import io
        for row in csv.reader(io.StringIO(run_out(["tasklist", "/fo", "csv", "/nh"]))):
            if len(row) < 5:
                continue
            digits = "".join(ch for ch in row[4] if ch.isdigit())
            if not digits:
                continue
            name = row[0][:-4] if row[0].lower().endswith(".exe") else row[0]
            apps[name] += int(digits) * 1024
        return apps.most_common(10)
    for ln in run_out(["ps", "-axo", "rss=,comm="]).splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rss, comm = ln.split(None, 1)
            rss = int(rss) * 1024
        except ValueError:
            continue
        name = comm.split(".app/")[0].rsplit("/", 1)[-1] if ".app/" in comm else comm.rsplit("/", 1)[-1]
        apps[name] += rss
    return apps.most_common(10)


NET = {"t": 0.0, "rx": 0, "tx": 0, "iface": ""}


def net_counters():
    """(interface, bytes received, bytes sent) since the computer started, or None."""
    try:
        import psutil
        c = psutil.net_io_counters()
        return "all", c.bytes_recv, c.bytes_sent
    except Exception:
        pass
    try:
        if PLATFORM == "darwin":
            iface = ""
            for ln in run_out(["route", "-n", "get", "default"]).splitlines():
                if "interface:" in ln:
                    iface = ln.split("interface:")[1].strip()
            tot = {}
            for ln in run_out(["netstat", "-ib"]).splitlines()[1:]:
                p = ln.split()
                if len(p) < 10 or not p[2].startswith("<Link#"):
                    continue
                try:
                    # Name Mtu Network [Address] Ipkts Ierrs Ibytes Opkts Oerrs Obytes Coll
                    tot[p[0].rstrip("*")] = (int(p[-5]), int(p[-2]))
                except ValueError:
                    continue
            if iface in tot:
                return (iface,) + tot[iface]
            en = [v for k, v in tot.items() if k.startswith("en")]
            if en:
                return "all", sum(v[0] for v in en), sum(v[1] for v in en)
            return None
        if PLATFORM == "win32":
            # The first row of numbers in "netstat -e" is bytes received and sent, in any language.
            for ln in run_out(["netstat", "-e"]).splitlines():
                p = ln.split()
                if len(p) >= 3 and p[-1].isdigit() and p[-2].isdigit():
                    return "all", int(p[-2]), int(p[-1])
            return None
        best = None
        with open("/proc/net/dev") as fh:
            for ln in fh.read().splitlines()[2:]:
                name, rest = ln.split(":", 1)
                name = name.strip(); p = rest.split()
                if name == "lo":
                    continue
                v = (int(p[0]), int(p[8]))
                if best is None or v[0] > best[1][0]:
                    best = (name, v)
        return (best[0],) + best[1] if best else None
    except Exception:
        return None


def net_now():
    c = net_counters()
    if not c:
        return None
    iface, rx, tx = c
    now = time.time()
    down = up = None
    if NET["t"] and NET["iface"] == iface and now - NET["t"] > 0.3 and rx >= NET["rx"] and tx >= NET["tx"]:
        dt = now - NET["t"]
        down = (rx - NET["rx"]) / dt
        up = (tx - NET["tx"]) / dt
    NET.update(t=now, rx=rx, tx=tx, iface=iface)
    return {"iface": iface, "rx": rx, "tx": tx, "down": down, "up": up}


def system_now():
    du = shutil.disk_usage(HOME)
    return {"at": int(time.time()), "memory": memory_now(), "apps": top_apps(), "network": net_now(),
            "disk": {"totalGb": round(du.total / 1e9, 1), "usedGb": round(du.used / 1e9, 1), "freeGb": round(du.free / 1e9, 1)}}


# ---------------------------------------------------------------- files

class Refused(Exception):
    pass


def resolve(relpath):
    """Turn a path from the page ("Documents/a.txt") into a real path inside the home folder."""
    parts = [p for p in str(relpath or "").replace("\\", "/").split("/")]
    if not parts or any(p in ("", ".", "..") for p in parts):
        raise Refused("That path is not valid.")
    p = os.path.join(HOME, *parts)
    real = os.path.realpath(p)
    home = os.path.realpath(HOME)
    nc = os.path.normcase
    if not (nc(real) == nc(home) or nc(real).startswith(nc(home) + nc(os.sep))):
        raise Refused("That file is outside the home folder.")
    if not os.path.exists(real):
        raise Refused("That file is not where the scan found it.")
    return real


def open_path(path, reveal):
    if not reveal:
        if not os.path.isfile(path) or path.lower().endswith(NO_OPEN) or (PLATFORM != "win32" and os.access(path, os.X_OK)):
            raise Refused("This kind of file is shown in its folder instead of opened.")
    if PLATFORM == "darwin":
        subprocess.Popen(["open", "-R", path] if reveal else ["open", path])
    elif PLATFORM == "win32":
        if reveal:
            subprocess.Popen('explorer /select,"%s"' % path)
        else:
            os.startfile(path)  # noqa: the extension list above keeps programs out
    else:
        subprocess.Popen(["xdg-open", os.path.dirname(path) if reveal else path])


def same_bytes(a, b):
    try:
        if os.path.getsize(a) != os.path.getsize(b):
            return False
        with open(a, "rb") as fa, open(b, "rb") as fb:
            while True:
                x = fa.read(1 << 20)
                y = fb.read(1 << 20)
                if x != y:
                    return False
                if not x:
                    return True
    except OSError:
        return False


def to_trash(path):
    """Move one file to the Trash or Recycle Bin. Never deletes outright."""
    if PLATFORM == "darwin":
        script = ('on run argv\n tell application "Finder" to delete (POSIX file (item 1 of argv) as alias)\nend run')
        r = subprocess.run(["osascript", "-e", script, path], capture_output=True, text=True, timeout=60)
        if os.path.exists(path):
            raise Refused((r.stderr or "Finder did not move it").strip()[:160])
        return
    if PLATFORM == "win32":
        import ctypes
        from ctypes import wintypes

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _pack_ = 1 if ctypes.sizeof(ctypes.c_void_p) == 4 else 8
            _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                        ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL),
                        ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]
        op = SHFILEOPSTRUCTW()
        op.wFunc = 3  # FO_DELETE
        op.pFrom = path + "\0"
        op.fFlags = 0x40 | 0x10 | 0x4 | 0x400  # ALLOWUNDO | NOCONFIRMATION | SILENT | NOERRORUI
        rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        if rc != 0 or op.fAnyOperationsAborted or os.path.exists(path):
            raise Refused("Windows did not move it to the Recycle Bin (code %s)." % rc)
        return
    if shutil.which("gio"):
        subprocess.run(["gio", "trash", path], capture_output=True, timeout=60)
        if not os.path.exists(path):
            return
    base = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share"), "Trash")
    os.makedirs(os.path.join(base, "files"), exist_ok=True)
    os.makedirs(os.path.join(base, "info"), exist_ok=True)
    name = os.path.basename(path)
    stem, ext = os.path.splitext(name)
    k = 1
    while os.path.exists(os.path.join(base, "files", name)) or os.path.exists(os.path.join(base, "info", name + ".trashinfo")):
        k += 1
        name = "%s.%d%s" % (stem, k, ext)
    with open(os.path.join(base, "info", name + ".trashinfo"), "w", encoding="utf-8") as fh:
        fh.write("[Trash Info]\nPath=%s\nDeletionDate=%s\n" % (urllib.parse.quote(path), time.strftime("%Y-%m-%dT%H:%M:%S")))
    try:
        os.rename(path, os.path.join(base, "files", name))
    except OSError:
        os.remove(os.path.join(base, "info", name + ".trashinfo"))
        raise Refused("That file is on another drive than the Trash.")


def trash_copies(items):
    """Each item: {"rel": copy to remove, "keep": [copies being kept]}. A copy only moves if it matches a kept one byte for byte."""
    out = []
    for it in items[:2000]:
        r = {"rel": it.get("rel"), "ok": False}
        try:
            target = resolve(it.get("rel"))
            if not os.path.isfile(target):
                raise Refused("Not a file.")
            keeps = []
            for k in it.get("keep") or []:
                try:
                    kp = resolve(k)
                except Refused:
                    continue
                if os.path.normcase(kp) != os.path.normcase(target) and os.path.isfile(kp):
                    keeps.append(kp)
            if not keeps:
                raise Refused("No kept copy was found, so this one stays.")
            if not any(same_bytes(target, kp) for kp in keeps):
                raise Refused("Its contents differ from the copy being kept, so it stays.")
            to_trash(target)
            r["ok"] = True
        except Refused as e:
            r["error"] = str(e)
        except Exception as e:
            r["error"] = "%s: %s" % (type(e).__name__, e)
        out.append(r)
    return out


# ---------------------------------------------------------------- server

KEY = secrets.token_urlsafe(24)
PORT = [0]


def cookie_name():
    return "starmap%d" % PORT[0]
STATIC = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
          ".woff2": "font/woff2", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".txt": "text/plain; charset=utf-8"}


class Handler(BaseHTTPRequestHandler):
    server_version = "StarMap/" + VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    # -- helpers
    def send(self, code, body=b"", ctype="application/json", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def host_ok(self):
        host = (self.headers.get("Host") or "").lower()
        return host in ("127.0.0.1:%d" % PORT[0], "localhost:%d" % PORT[0])

    def authed(self):
        if not self.host_ok():
            return False
        cookies = {}
        for part in (self.headers.get("Cookie") or "").split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                cookies[k] = v
        return secrets.compare_digest(cookies.get(cookie_name(), ""), KEY)

    def origin_ok(self):
        o = self.headers.get("Origin")
        return o is None or o in ("http://127.0.0.1:%d" % PORT[0], "http://localhost:%d" % PORT[0])

    def body_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 5_000_000:
            raise Refused("Request too large.")
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw or b"{}")

    # -- routes
    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        path = url.path
        q = urllib.parse.parse_qs(url.query)
        if not self.host_ok():
            return self.send(421, {"error": "Open StarMap at the address it printed when it started."})
        if path == "/":
            if q.get("k", [""])[0] and secrets.compare_digest(q["k"][0], KEY):
                cookie = "%s=%s; HttpOnly; SameSite=Strict; Path=/" % (cookie_name(), KEY)
                return self.send(302, b"", "text/plain", {"Location": "/", "Set-Cookie": cookie})
            return self.static("index.html")
        if path.startswith("/vendor/") or path.startswith("/fonts/") or path in ("/favicon.svg",):
            return self.static(path.lstrip("/"))
        if not self.authed():
            return self.send(403, {"error": "locked"})
        if path == "/api/info":
            return self.send(200, {"app": APP, "version": VERSION, "platform": PLATFORM, "home": HOME, "sep": os.sep,
                                   "sysDir": SYS_DIR, "hasScan": os.path.exists(scan_file()), "state": S["state"]})
        if path == "/api/data":
            p = scan_file()
            if not os.path.exists(p):
                return self.send(404, {"error": "no scan yet"})
            with open(p, "rb") as fh:
                return self.send(200, fh.read())
        if path == "/api/progress":
            el = time.time() - S["t0"] if S["t0"] else 0
            pct = min(99.0, S["seen"] / S["prev"] * 100) if S["prev"] else None
            return self.send(200, {"state": S["state"], "seen": S["seen"], "where": S["where"], "stage": S["stage"],
                                   "elapsed": round(el, 1), "pct": pct, "error": S["error"]})
        if path == "/api/system":
            return self.send(200, system_now())
        if path == "/file":
            return self.serve_file(q.get("rel", [""])[0])
        return self.send(404, {"error": "unknown"})

    def do_HEAD(self):
        return self.do_GET()

    def do_POST(self):
        if not (self.authed() and self.origin_ok()):
            return self.send(403, {"error": "locked"})
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self.send(415, {"error": "Send JSON."})
        try:
            body = self.body_json()
        except Exception:
            return self.send(400, {"error": "Bad request."})
        try:
            if self.path == "/api/scan":
                with LOCK:
                    if S["state"] not in ("running", "stopping"):
                        S.update(state="running", seen=0, where="", t0=time.time(), prev=int(body.get("prev") or 0), error="", stage="Starting")
                        threading.Thread(target=run_scan, daemon=True).start()
                return self.send(200, {"ok": True})
            if self.path == "/api/stop":
                if S["state"] == "running":
                    S["state"] = "stopping"
                return self.send(200, {"ok": True})
            if self.path in ("/api/open", "/api/reveal"):
                open_path(resolve(body.get("rel")), self.path == "/api/reveal")
                return self.send(200, {"ok": True})
            if self.path == "/api/trash":
                return self.send(200, {"results": trash_copies(body.get("items") or [])})
        except Refused as e:
            return self.send(400, {"error": str(e)})
        except Exception as e:
            return self.send(500, {"error": "%s: %s" % (type(e).__name__, e)})
        return self.send(404, {"error": "unknown"})

    def static(self, relp):
        full = os.path.realpath(os.path.join(WEB_DIR, *relp.split("/")))
        if not full.startswith(os.path.realpath(WEB_DIR) + os.sep) or not os.path.isfile(full):
            return self.send(404, {"error": "not found"})
        ctype = STATIC.get(os.path.splitext(full)[1].lower(), "application/octet-stream")
        with open(full, "rb") as fh:
            data = fh.read()
        headers = {}
        if relp == "index.html":
            headers["Content-Security-Policy"] = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                                                  "img-src 'self' data: blob:; media-src 'self' blob:; font-src 'self'; connect-src 'self'; "
                                                  "frame-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'")
        return self.send(200, data, ctype, headers)

    def serve_file(self, relp):
        try:
            path = resolve(relp)
        except Refused as e:
            return self.send(404, {"error": str(e)})
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        if ext not in PREVIEW_TYPES or not os.path.isfile(path):
            return self.send(415, {"error": "No preview for this type."})
        size = os.path.getsize(path)
        start, end = 0, size - 1
        rng = self.headers.get("Range")
        code = 200
        if rng and rng.startswith("bytes="):
            try:
                a, b = rng[6:].split(",")[0].split("-")
                if a == "":
                    start = max(0, size - int(b))
                else:
                    start = int(a)
                    end = min(size - 1, int(b)) if b else size - 1
                if start > end or start >= size:
                    return self.send(416, b"", "text/plain", {"Content-Range": "bytes */%d" % size})
                code = 206
            except ValueError:
                start, end = 0, size - 1
        length = max(0, end - start + 1)
        self.send_response(code)
        self.send_header("Content-Type", PREVIEW_TYPES[ext])
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if ext != "pdf":  # files from disk can never run script as part of StarMap
            self.send_header("Content-Security-Policy", "sandbox; default-src 'none'; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline'")
        if code == 206:
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            with open(path, "rb") as fh:
                fh.seek(start)
                left = length
                while left > 0:
                    chunk = fh.read(min(1 << 16, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (ConnectionError, OSError):
            pass


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def handle_error(self, request, client_address):
        # Browsers drop connections all the time (seeking in a video, closing a tab). Stay quiet about those.
        if isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            return
        super().handle_error(request, client_address)


def make_server(port):
    for p in ([port] if port else list(range(DEFAULT_PORT, DEFAULT_PORT + 10)) + [0]):
        try:
            srv = Server(("127.0.0.1", p), Handler)
            PORT[0] = srv.server_address[1]
            return srv
        except OSError:
            continue
    raise SystemExit("StarMap could not find a free port on this computer.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=APP)
    ap.add_argument("--port", type=int, default=0, help="port to use on 127.0.0.1 (default: %d, or the next free one)" % DEFAULT_PORT)
    ap.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    ap.add_argument("--version", action="version", version="%s %s" % (APP, VERSION))
    args = ap.parse_args(argv)
    if sys.version_info < (3, 9):
        raise SystemExit("StarMap needs Python 3.9 or newer.")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")  # a home folder name the console cannot show must not stop StarMap
        except Exception:
            pass
    if not os.path.isfile(os.path.join(WEB_DIR, "index.html")):
        raise SystemExit("The web folder is missing. Keep starmap.py next to the web folder it came with.")
    srv = make_server(args.port)
    url = "http://127.0.0.1:%d/?k=%s" % (PORT[0], KEY)
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    print("")
    print("  %s %s" % (APP, VERSION))
    print("  Mapping: %s" % HOME)
    print("")
    print("  Open this address if the browser does not open by itself:")
    print("  " + url)
    print("")
    print("  Leave this window open while you use the map. Press Ctrl+C to stop.")
    print("")
    sys.stdout.flush()
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\n  StarMap stopped.")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
