# Live readouts

Beside the left panel and at the top right, StarMap shows live figures that update every three seconds.

## Disk

How much of the disk is used, its size and free space, with a bar split into:

- files in your home folder
- app and dependency bundles (the nebulae)
- the system folder in your home folder: Library on macOS, AppData on Windows
- apps and system folders outside your home folder
- space in use that the scan couldn't locate
- other volumes on the same disk, when the system reports them
- free space

The total updates live; the split comes from the last scan.

## Memory

How much memory is in use, with a bar split into:

- **Apps:** memory apps are using
- **Wired:** memory the system has locked for itself (macOS)
- **Compressed:** memory macOS has compressed to make room
- **Cached:** files kept in memory to open faster, which is released when apps need it
- **Free**

Underneath are the three apps using the most memory. On Windows, unless the optional `psutil` package is installed, memory is shown as used and free only.

## Network

Download and upload speed across your network connection, the totals received and sent since the computer started, and two bars that fill relative to the recent peak speed, so they show how busy the connection is.

## Minimal view

Each readout has a small **–** button. It hides the text and leaves just the icon and bars; **+** brings the text back. StarMap remembers your choice.

## More detail with psutil

If the [`psutil`](https://pypi.org/project/psutil/) package is installed, StarMap uses it for memory, the app list and network. Otherwise it uses each system's built-in tools (`vm_stat`, `netstat` and `ps` on macOS; Windows' memory API, `tasklist` and `netstat` on Windows; `/proc` on Linux).

```
python3 -m pip install psutil
```
