# Recommendations

The bar across the top lists what could free the most space on this computer, biggest first. Click one for the reasons, the steps and any commands. StarMap only suggests; it never runs a command or deletes anything by itself.

## How safe each one is

| Mark | Meaning |
|---|---|
| **Safe to clear** (green) | Caches and leftovers that are rebuilt automatically when needed. |
| **Check first** (gold) | Probably safe, but decide what to keep before removing anything. |
| **Look here first** (red) | Space the scan couldn't locate, and where to find it. |

**Copy commands** puts the commands on the clipboard. Paste them into Terminal (macOS, Linux) or PowerShell (Windows).

## On every system

- **Track down the remaining space.** Where the space the scan couldn't measure usually is, and how to see it with the system's own storage settings.
- **Trim the history of a project.** A project's `.git` folder is very large, which usually means big files were committed at some point. The command lists the largest objects in the history. Removing them rewrites history, so push or back up the project first. Never delete a `.git` folder by hand.
- **Move large archives off this computer.** Single archive files over 1.5 GB.
- **Thin out old archives.** Folders holding five or more archives that add up to over 1 GB, such as repeated backups or old builds.
- **Clear package caches.** Downloads kept by npm, pip, Yarn and, on macOS, Homebrew. They download again when needed.
- **Remove spare copies.** Opens the [duplicate review](Cleaning-Up-Duplicates).

## macOS only

- **Remove unused iOS simulators.** Simulators that the installed Xcode can no longer run.
- **Clear Xcode device support.** Debug symbols for every iOS version Xcode has connected to, and build leftovers.
- **Clear large app caches.** Apps keeping more than 500 MB in `~/Library/Caches`. Quit those apps first.

## Windows only

- **Clear temporary files.** The temporary folder in AppData. Files still in use are skipped.

## Linux only

- **Clear the cache folder.** `~/.cache`, which apps rebuild as needed.

A recommendation only appears when there's enough to gain: at least 200 MB, or 15 GB for **Track down the remaining space**.
