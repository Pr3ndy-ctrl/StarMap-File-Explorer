# Troubleshooting

## Starting

**macOS says StarMap.command "can't be opened" or can't be checked.**
Right-click it, choose **Open**, then **Open** again. Or run `python3 starmap.py` in Terminal from the StarMap folder.

**macOS says StarMap.command can't be run because of permissions.**
The ZIP may have lost its executable flag. In Terminal, in the StarMap folder, run `chmod +x StarMap.command`.

**Windows shows "Windows protected your PC".**
Click **More info**, then **Run anyway**.

**"StarMap needs Python 3.9 or newer".**
Install Python; see [Getting started](Getting-Started).

**On Windows, typing `python` opens the Microsoft Store.**
That's a Windows shortcut, not Python. Install Python from python.org with **Add python.exe to PATH** ticked, or use `py starmap.py`.

**The browser didn't open.**
Copy the address StarMap printed in its window (it starts with `http://127.0.0.1:`) into your browser.

**"This page is locked".**
The tab is from an earlier run: each start creates a new key. Use the address StarMap printed this time.

**"StarMap is not running".**
Its window was closed or it was stopped. Start it again, then reload the page.

## Scanning

**Documents, Desktop or Downloads are missing on a Mac.**
macOS didn't give Terminal access. Open System Settings, Privacy & Security, Files and Folders, find Terminal and switch those folders on. Then **Re-scan**.

**The scan is slow.**
The first scan of a full drive takes a few minutes, mostly measuring the system folder and folders outside your home folder. To skip the outside folders, start StarMap with `STARMAP_OUTSIDE` set empty (see [Options and settings](Options-and-Settings)).

**The map is slow or jerky.**
Untick **Copy arcs**, **Folder lines** and **Slow rotation**, or use a browser with hardware graphics switched on.

**The numbers don't match Finder or File Explorer.**
StarMap counts space on disk, while some tools count file sizes. Space it couldn't reach is shown as not accounted for; see [Where the space goes](Where-the-Space-Goes).

## Files

**A video won't play.**
Your browser may not support the format. Use **Open file** to play it in its usual app.

**"Open file" says it shows the file in its folder instead.**
StarMap won't open programs, scripts or installers. Use **Show in Finder** or **Show in File Explorer**.

**Moving copies to the Trash fails on a Mac.**
macOS needs to let Terminal control Finder. Open System Settings, Privacy & Security, Automation, find Terminal and switch on Finder.

## Still stuck?

Open an [issue](https://github.com/Pr3ndy-ctrl/StarMap-File-Explorer/issues) and include your operating system, your Python version (`python3 --version`) and what StarMap's window says.
