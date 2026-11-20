"""
Smoke tests for StarMap. They build a small fake home folder, scan it, start the
local server and exercise every endpoint the page uses. Standard library only:

    python -m unittest discover -s tests -v
"""

import http.client
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="starmap-test-")
HOME = os.path.join(TMP, "home")
os.environ["STARMAP_HOME"] = HOME
os.environ["STARMAP_DATA"] = os.path.join(TMP, "data")
os.environ["STARMAP_OUTSIDE"] = ""
os.environ["XDG_DATA_HOME"] = os.path.join(TMP, "xdg")  # Linux trash stays on the same drive as the test files


def write(rel, data):
    p = os.path.join(HOME, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(data)
    return p


write("Documents/notes.md", b"# notes\n")
write("Documents/report.pdf", b"%PDF-1.4\n" + b"x" * 4000)
write("Documents/run.sh", b"#!/bin/sh\necho hi\n")
write("Documents/tool.exe", b"MZ" + b"\0" * 100)
write("Music/song.mp3", bytes(range(256)) * 40)
same = os.urandom(70000)
write("Photos/a/dup.bin", same)
write("Photos/b/dup.bin", same)
write("Photos/c/dup.bin", os.urandom(70000))
write("Projects/app/package.json", b"{}")
for i in range(30):
    write("Projects/app/node_modules/pkg/f%d.js" % i, b"module.exports=1\n")
write("Projects/app/.git/objects/pack", b"p" * 5000)
write("Videos/clip.mp4", b"\0" * 5000)

LOOP = None
if os.name == "nt":
    LOOP = os.path.join(HOME, "Photos", "loop")
    subprocess.run(["cmd", "/c", "mklink", "/J", LOOP, HOME], capture_output=True)
else:
    try:
        LOOP = os.path.join(HOME, "Photos", "loop")
        os.symlink(HOME, LOOP)
    except OSError:
        LOOP = None

spec = importlib.util.spec_from_file_location("starmap", os.path.join(ROOT, "starmap.py"))
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)


def path_of(dirs, d):
    a = []
    while d > 0:
        a.append(dirs[d][0]); d = dirs[d][1]
    return "/".join(reversed(a))


class ScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sm.S.update(state="running", seen=0, prev=0)
        cls.pack = sm.scan()
        sm.S.update(state="idle")

    def test_files_and_folders(self):
        names = {f[0] for f in self.pack["files"]}
        for n in ("notes.md", "report.pdf", "song.mp3", "dup.bin", "package.json", "clip.mp4"):
            self.assertIn(n, names)
        self.assertNotIn("f0.js", names, "node_modules should be a nebula, not stars")

    def test_nebulae_are_counted(self):
        dirs = self.pack["dirs"]
        neb = {path_of(dirs, i): d for i, d in enumerate(dirs) if d[2] == 1}
        self.assertEqual(neb["Projects/app/node_modules"][3], 30)
        self.assertIn("Projects/app/.git", neb)

    def test_links_are_not_followed(self):
        if not LOOP or not os.path.lexists(LOOP):
            self.skipTest("this system would not create a link")
        dirs = self.pack["dirs"]
        self.assertNotIn("Photos/loop", {path_of(dirs, i) for i in range(len(dirs))})

    def test_copies_compare_contents(self):
        files, dirs, sig = self.pack["files"], self.pack["dirs"], self.pack["extra"]["sig"]
        by = {path_of(dirs, f[1]): sig.get(str(i)) for i, f in enumerate(files) if f[0] == "dup.bin"}
        self.assertEqual(by["Photos/a"], by["Photos/b"])
        self.assertNotEqual(by["Photos/a"], by["Photos/c"])

    def test_disk_figures(self):
        d = self.pack["extra"]["disk"]
        self.assertGreater(d["totalGb"], 0)
        self.assertGreaterEqual(d["freeGb"], 0)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = sm.make_server(0)
        cls.port = sm.PORT[0]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        c = http.client.HTTPConnection("127.0.0.1", cls.port, timeout=10)
        c.request("GET", "/?k=" + sm.KEY)
        r = c.getresponse(); r.read()
        c.close()
        assert r.status == 302, r.status
        cls.cookie = r.getheader("Set-Cookie").split(";")[0]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def req(self, method, path, body=None, headers=None, auth=True):
        h = {"Host": "127.0.0.1:%d" % self.port}
        if auth:
            h["Cookie"] = self.cookie
        if body is not None:
            body = json.dumps(body).encode()
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        c.request(method, path, body=body, headers=h)
        r = c.getresponse()
        data = r.read()
        c.close()
        return r, data

    def test_locked_without_key(self):
        r, _ = self.req("GET", "/api/info", auth=False)
        self.assertEqual(r.status, 403)

    def test_wrong_host_refused(self):
        r, _ = self.req("GET", "/api/info", headers={"Host": "evil.example:%d" % self.port})
        self.assertEqual(r.status, 421)

    def test_other_origin_refused(self):
        r, _ = self.req("POST", "/api/stop", body={}, headers={"Origin": "https://evil.example"})
        self.assertEqual(r.status, 403)

    def test_page_and_vendor_files(self):
        r, d = self.req("GET", "/", auth=False)
        self.assertEqual(r.status, 200)
        self.assertIn(b"<title>", d)
        r, d = self.req("GET", "/vendor/three.min.js", auth=False)
        self.assertEqual(r.status, 200)
        r, _ = self.req("GET", "/vendor/../starmap.py", auth=False)
        self.assertEqual(r.status, 404)

    def test_info(self):
        r, d = self.req("GET", "/api/info")
        self.assertEqual(r.status, 200)
        j = json.loads(d)
        self.assertEqual(j["platform"], sm.PLATFORM)
        self.assertEqual(os.path.normcase(j["home"]), os.path.normcase(HOME))

    def test_scan_then_data(self):
        r, _ = self.req("POST", "/api/scan", body={"prev": 0})
        self.assertEqual(r.status, 200)
        for _ in range(600):
            time.sleep(0.1)
            p = json.loads(self.req("GET", "/api/progress")[1])
            if p["state"] not in ("running", "stopping"):
                break
        self.assertEqual(p["state"], "done", p)
        r, d = self.req("GET", "/api/data")
        self.assertEqual(r.status, 200)
        j = json.loads(d)
        self.assertTrue(j["files"])

    def test_file_ranges(self):
        r, d = self.req("GET", "/file?rel=Music/song.mp3", headers={"Range": "bytes=0-9"})
        self.assertEqual(r.status, 206)
        self.assertEqual(d, bytes(range(10)))
        self.assertEqual(r.getheader("Content-Type"), "audio/mpeg")
        r, d = self.req("GET", "/file?rel=Music/song.mp3")
        self.assertEqual(r.status, 200)
        self.assertEqual(len(d), 256 * 40)

    def test_file_stays_inside_home(self):
        for bad in ("../outside.txt", "Music/../../x", "", "/etc/passwd", "C:/Windows/win.ini"):
            r, _ = self.req("GET", "/file?rel=" + bad)
            self.assertIn(r.status, (404, 415), bad)

    def test_text_is_served_as_plain_text(self):
        r, _ = self.req("GET", "/file?rel=Documents/notes.md")
        self.assertTrue(r.getheader("Content-Type").startswith("text/plain"))
        self.assertIn("sandbox", r.getheader("Content-Security-Policy"))

    def test_programs_are_never_opened(self):
        for rel in ("Documents/run.sh", "Documents/tool.exe"):
            r, d = self.req("POST", "/api/open", body={"rel": rel})
            self.assertEqual(r.status, 400, rel)

    def test_system_readouts(self):
        r, d = self.req("GET", "/api/system")
        self.assertEqual(r.status, 200)
        j = json.loads(d)
        self.assertIsNotNone(j["memory"], "memory could not be read on " + sys.platform)
        self.assertGreater(j["memory"]["total"], 0)
        self.assertTrue(j["apps"], "no processes were listed on " + sys.platform)
        self.assertIsNotNone(j["network"], "network could not be read on " + sys.platform)
        time.sleep(1.1)
        j = json.loads(self.req("GET", "/api/system")[1])
        self.assertIsNotNone(j["network"]["down"])
        self.assertGreaterEqual(j["network"]["down"], 0)

    def test_trash_checks_contents_first(self):
        r, d = self.req("POST", "/api/trash", body={"items": [{"rel": "Photos/c/dup.bin", "keep": ["Photos/a/dup.bin"]}]})
        res = json.loads(d)["results"][0]
        self.assertFalse(res["ok"])
        self.assertTrue(os.path.exists(os.path.join(HOME, "Photos", "c", "dup.bin")))
        r, d = self.req("POST", "/api/trash", body={"items": [{"rel": "Photos/b/dup.bin", "keep": []}]})
        self.assertFalse(json.loads(d)["results"][0]["ok"])

    def test_trash_moves_identical_copy(self):
        target = os.path.join(HOME, "Photos", "b", "dup.bin")
        r, d = self.req("POST", "/api/trash", body={"items": [{"rel": "Photos/b/dup.bin", "keep": ["Photos/a/dup.bin"]}]})
        res = json.loads(d)["results"][0]
        if sys.platform == "darwin" and not res["ok"]:
            self.skipTest("Finder automation is not available here: " + res.get("error", ""))
        self.assertTrue(res["ok"], res)
        self.assertFalse(os.path.exists(target))
        self.assertTrue(os.path.exists(os.path.join(HOME, "Photos", "a", "dup.bin")))


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
