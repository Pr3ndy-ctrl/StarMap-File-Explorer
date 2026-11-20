#!/usr/bin/env python3
"""
Builds a made-up home folder full of small sample files, so StarMap can be tried,
tested or screenshotted without showing anyone's real files.

    python3 tools/demo_home.py /tmp/demo-home
    STARMAP_HOME=/tmp/demo-home STARMAP_OUTSIDE= python3 starmap.py

(On Windows: set STARMAP_HOME=C:\\temp\\demo-home and set STARMAP_OUTSIDE= first.)
Files are tiny but their sizes on the map are realistic: each one is sparse
where the file system allows it.
"""

import os
import random
import sys
import time

rng = random.Random(7)
NOW = time.time()


def put(root, rel, size):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        head = rng.randbytes(min(size, 4096)) if hasattr(rng, "randbytes") else os.urandom(min(size, 4096))
        fh.write(head)
        if size > len(head):
            fh.seek(size - 1)
            fh.write(b"\0")
    t = NOW - rng.uniform(0, 3 * 365 * 86400) ** 1.0
    os.utime(p, (t, t))


def build(root):
    words = ("north harbour summit atlas river cedar orbit lumen quartz meadow ember signal".split())
    for y in (2023, 2024, 2025, 2026):
        for m in range(1, 13):
            put(root, "Documents/Invoices/%d/invoice-%d-%02d.pdf" % (y, y, m), rng.randint(60_000, 400_000))
    for i in range(40):
        put(root, "Documents/Notes/%s-%d.md" % (rng.choice(words), i), rng.randint(800, 30_000))
    for i in range(18):
        put(root, "Documents/Reports/report-%s-%d.docx" % (rng.choice(words), i), rng.randint(40_000, 2_000_000))
    for i in range(12):
        put(root, "Documents/Spreadsheets/budget-%d.xlsx" % i, rng.randint(20_000, 900_000))
    for album in ("Night Drive", "Coastline", "Field Recordings", "Live at the Hall"):
        for t in range(1, 13):
            put(root, "Music/%s/%02d %s.mp3" % (album, t, rng.choice(words).title()), rng.randint(3_000_000, 11_000_000))
    for y in (2024, 2025, 2026):
        for m in range(1, 13):
            for k in range(rng.randint(6, 26)):
                put(root, "Pictures/%d/%02d/IMG_%d%02d_%04d.jpg" % (y, m, y, m, k), rng.randint(1_500_000, 6_500_000))
    for i in range(14):
        put(root, "Movies/clip-%s-%d.mp4" % (rng.choice(words), i), rng.randint(40_000_000, 900_000_000))
    for proj in ("website", "mobile-app", "data-tools"):
        base = "Projects/" + proj
        put(root, base + "/package.json", 1200)
        put(root, base + "/README.md", 3000)
        for i in range(60):
            ext = rng.choice(["ts", "tsx", "js", "css", "py", "json"])
            put(root, "%s/src/%s/%s-%d.%s" % (base, rng.choice(["components", "lib", "pages", "api"]), rng.choice(words), i, ext), rng.randint(500, 40_000))
        for i in range(300):
            put(root, "%s/node_modules/pkg-%d/index.js" % (base, i), rng.randint(500, 200_000))
        for i in range(40):
            put(root, "%s/.git/objects/%02x/%s" % (base, i, "%038x" % rng.getrandbits(152)), rng.randint(1000, 4_000_000))
        for i in range(6):
            put(root, "%s/builds/build-%d.zip" % (base, i), rng.randint(200_000_000, 400_000_000))
    for i in range(30):
        put(root, "Downloads/%s-setup-%d.dmg" % (rng.choice(words), i), rng.randint(5_000_000, 300_000_000))
        put(root, "Downloads/%s-%d.pdf" % (rng.choice(words), i), rng.randint(100_000, 9_000_000))
    put(root, "Downloads/archive-2022.zip", 2_400_000_000)
    for i in range(10):
        put(root, "Desktop/screenshot-%d.png" % i, rng.randint(300_000, 3_000_000))
    same = rng.randbytes(90_000) if hasattr(rng, "randbytes") else os.urandom(90_000)
    for d in ("Documents/Reports", "Downloads", "Desktop"):
        p = os.path.join(root, *d.split("/"), "contract-final.pdf")
        with open(p, "wb") as fh:
            fh.write(same)
    for i in range(200):
        put(root, ".cache/thumbnails/t%d.png" % i, rng.randint(5_000, 60_000))
    samples(root)


def samples(root):
    """A few real files, so previews and playback can be tried."""
    import math
    import struct
    import wave
    import zlib

    def path(rel):
        p = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p

    with wave.open(path("Music/Field Recordings/tone.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
        w.writeframes(b"".join(struct.pack("<h", int(9000 * math.sin(2 * math.pi * 440 * t / 22050) * min(1, (22050 * 2 - t) / 4000)))
                               for t in range(22050 * 2)))
    wdt, hgt = 480, 300
    rows = b"".join(b"\0" + bytes(c for x in range(wdt) for c in (20 + x * 200 // wdt, 40 + y * 120 // hgt, 90 + (x + y) % 120)) for y in range(hgt))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path("Pictures/sample-gradient.png"), "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", wdt, hgt, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
    text = "Welcome to StarMap. This is a sample document."
    content = ("BT /F1 18 Tf 60 720 Td (%s) Tj ET" % text).encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out = b"%PDF-1.4\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    with open(path("Documents/Welcome.pdf"), "wb") as fh:
        fh.write(out)
    with open(path("Documents/Welcome.md"), "w", encoding="utf-8") as fh:
        fh.write("# Welcome\n\nThis sample home folder was made by tools/demo_home.py.\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: demo_home.py <empty folder to create>")
    root = os.path.abspath(sys.argv[1])
    if os.path.exists(root) and os.listdir(root):
        raise SystemExit("Choose a new or empty folder; this script will not write into one that has files.")
    build(root)
    print("Made a sample home folder at", root)
