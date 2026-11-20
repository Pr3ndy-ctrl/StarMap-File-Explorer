# Where the space goes

Click **Where the space goes** in the left panel for a breakdown of the disk.

## The figures at the top

- **Measured in this scan:** everything StarMap could add up: your files, the bundles and nebulae, the system folder in your home folder and the main folders outside it.
- **Not accounted for:** space the disk reports as used that the scan couldn't find. A paragraph underneath explains what StarMap couldn't reach.

## The sections

- **Biggest single items:** the largest files and bundles anywhere in the scan. Click one to fly to it.
- **By region of the home folder:** totals for each top-level folder, such as Documents, Downloads and Pictures.
- **Library (macOS) or AppData (Windows):** the folder where apps keep their settings, caches and data. It's measured piece by piece, and its biggest parts are listed by name.
- **Outside the home folder:** Applications and system folders (macOS), Program Files, ProgramData, Windows and the page and hibernation files (Windows), or `/usr`, `/opt`, `/var` and similar (Linux). Any marked "(part)" were too large to finish measuring in the time allowed.

## Why some space can't be accounted for

StarMap runs with your own permissions, so it can't measure:

- other people's accounts on the same computer
- protected system areas, such as parts of Library on macOS
- local Time Machine snapshots on macOS, which hold on to deleted files until macOS needs the space
- restore points and the component store on Windows
- other volumes that share the same disk, such as the macOS system volume

The **Track down the remaining space** recommendation shows where to look on your system, using its own storage settings.

The disk total and free space at the top are the figures the operating system reports, the same as `df` (macOS, Linux) or the drive's Properties (Windows). Finder may show more space as available, because it counts space macOS can free on its own.
