# Getting started

## What you need

- **Python 3.9 or newer.** Nothing else: StarMap uses only Python's standard library.
- A current web browser: Chrome, Edge, Firefox or Safari.

To check whether Python is installed, open Terminal (macOS, Linux) or PowerShell (Windows) and run `python3 --version` (Windows: `py --version`).

- **macOS:** running `python3` the first time offers to install Apple's command line developer tools, which include Python 3.9. Or install the latest Python from [python.org](https://www.python.org/downloads/).
- **Windows:** install Python from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH** on the first screen of the installer.
- **Linux:** install `python3` with your package manager. Most distributions already have it.

## Download

On the [repository page](https://github.com/Pr3ndy-ctrl/StarMap-File-Explorer), click **Code**, then **Download ZIP**, and unzip it somewhere you'll find again, such as your Documents folder. If you use Git:

```
git clone https://github.com/Pr3ndy-ctrl/StarMap-File-Explorer.git
```

Keep the folder together: `starmap.py` needs the `web` folder next to it.

## Start StarMap

### macOS

Double-click **StarMap.command**.

The first time, macOS may say it can't check the file for malicious software, because StarMap isn't signed by an Apple developer account. Right-click (or Control-click) `StarMap.command`, choose **Open**, then click **Open** again. You only need to do this once.

When the scan starts, macOS asks whether Terminal may access your Documents, Desktop and Downloads folders. Click **Allow** for each, or those folders will be left out of the map. You can change this later in System Settings, Privacy & Security, Files and Folders.

### Windows

Double-click **StarMap.bat**.

If a blue "Windows protected your PC" box appears, click **More info**, then **Run anyway**. Windows shows this for any downloaded script that isn't signed.

### Linux

Open a terminal in the StarMap folder and run:

```
./StarMap.sh
```

### From any terminal

```
python3 starmap.py        # macOS and Linux
py starmap.py             # Windows
```

## The first scan

StarMap opens the map in your browser and starts reading your home folder straight away. A progress bar shows what it's reading. On a full drive the first scan can take a few minutes; later visits open instantly from the saved scan, and **Re-scan** reads everything again.

## Stopping StarMap

StarMap runs in the small window that opened when you started it. Leave that window open while you use the map. To stop StarMap, close the window or press **Ctrl+C** in it. Closing the browser tab doesn't stop it.

Next: [Using the map](Using-the-Map).
