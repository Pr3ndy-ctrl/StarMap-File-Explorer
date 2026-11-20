"""
Starts StarMap the way a person would (python starmap.py), waits for the address
it prints, unlocks it with the key and asks it for /api/info. Used by CI on
macOS, Windows and Linux:

    python tests/check_launch.py
"""

import http.cookiejar
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    env = dict(os.environ, STARMAP_OUTSIDE="")
    proc = subprocess.Popen([sys.executable, "-u", os.path.join(ROOT, "starmap.py"), "--no-browser"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    lines, found = [], []

    def read():
        for ln in proc.stdout:
            lines.append(ln)
            m = re.search(r"http://127\.0\.0\.1:\d+/\?k=[A-Za-z0-9_-]+", ln)
            if m:
                found.append(m.group(0))

    threading.Thread(target=read, daemon=True).start()
    try:
        end = time.time() + 60
        while not found and time.time() < end and proc.poll() is None:
            time.sleep(0.2)
        print("".join(lines))
        if not found:
            raise SystemExit("StarMap did not print its address within 60 seconds.")
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        page = opener.open(found[0], timeout=20).read()
        assert b"<title>StarMap" in page, "the map page was not served"
        base = found[0].split("/?")[0]
        info = json.loads(opener.open(base + "/api/info", timeout=20).read())
        print(json.dumps(info, indent=2))
        assert info["platform"] in ("darwin", "win32", "linux"), info
        system = json.loads(opener.open(base + "/api/system", timeout=30).read())
        assert system["memory"] and system["memory"]["total"] > 0, system
        print("StarMap started and answered on", info["platform"])
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
