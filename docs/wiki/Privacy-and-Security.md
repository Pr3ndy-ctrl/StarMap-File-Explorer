# Privacy and security

## What StarMap reads

- File and folder **names, sizes and dates** in your home folder.
- Folder sizes in the system folder (Library or AppData) and the main folders outside your home folder, where your account may read them.
- A **64 KB sample from the start and end** of files that share a name and size with another file, to tell real copies apart. Files stored only in iCloud, OneDrive or similar are never downloaded for this.
- Live memory, network and app-memory figures from the operating system.

It doesn't read the contents of your files beyond those samples, except when you open a preview.

## What StarMap keeps

One file with the last scan, so the map opens instantly next time:

| System | Location |
|---|---|
| macOS | `~/Library/Application Support/StarMap/scan.json` |
| Windows | `%LOCALAPPDATA%\StarMap\scan.json` |
| Linux | `~/.local/share/starmap/scan.json` |

Delete that folder to remove everything StarMap has stored. Your browser also remembers a few display choices, such as which readouts are minimised and which copies you've ticked.

## What StarMap changes

Only two things, and only when you press the button:

- **Open file** asks your system to open a document. Programs, scripts and installers are refused.
- **Move ticked copies to the Trash** moves duplicate copies to the Trash or Recycle Bin, after a byte-for-byte check against a copy you keep. Nothing is deleted outright.

Recommendations show commands; StarMap never runs them.

## Nothing leaves your computer

StarMap serves the map from `127.0.0.1`, an address only your own computer can reach. The 3D library, fonts and document viewer are included with StarMap, so the page makes no requests to the internet, and StarMap has no analytics or update checks.

## How the local server is protected

- It listens on `127.0.0.1` only, never on your network.
- Every start creates a new random key. Your browser receives it once, from the address StarMap opens, and keeps it in a cookie that other websites can't read or send (`HttpOnly`, `SameSite=Strict`). Requests without it are refused.
- Requests must name `127.0.0.1` or `localhost` as the host, which blocks DNS-rebinding attacks. Changes must come from the StarMap page itself.
- It only serves files inside your home folder, only of the types it can preview, and with headers that stop them running as part of StarMap.

To report a security problem, use **Report a vulnerability** on the repository's Security tab rather than a public issue. See [SECURITY.md](https://github.com/Pr3ndy-ctrl/StarMap-File-Explorer/blob/main/SECURITY.md).
