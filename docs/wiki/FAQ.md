# FAQ

**Is StarMap free?**
Yes, under the MIT licence.

**Does it upload anything?**
No. It runs entirely on your computer and the page makes no requests to the internet. See [Privacy and security](Privacy-and-Security).

**Can it delete my files?**
It never deletes anything outright. The only thing that moves files is the duplicate review, which moves copies you tick to the Trash or Recycle Bin after checking that an identical copy is kept. See [Cleaning up duplicates](Cleaning-Up-Duplicates).

**Why does it need Python?**
Python lets one small program read your folders and draw the map on macOS, Windows and Linux without installing anything else.

**Why does it run in a browser?**
The browser draws the 3D map, plays media and shows documents. The page is served by StarMap on your own computer.

**Can I map a drive or folder other than my home folder?**
Yes: set `STARMAP_HOME` to the folder. See [Options and settings](Options-and-Settings).

**Can it map other computers or network drives?**
It maps whatever folder you point it at, including a mounted network drive, though scanning one is slower.

**Why are some folders violet clouds?**
They're full of machine-managed files, such as app bundles, `node_modules` or Library. Showing each file would hide your own. Click one to see its size and file count.

**Why is so much space "not accounted for"?**
Some of the disk is in places your account can't measure, such as system snapshots and other accounts. See [Where the space goes](Where-the-Space-Goes).

**Does it work on Apple silicon and on ARM Windows?**
Yes. StarMap is plain Python, so it runs wherever Python 3.9 or newer does.
