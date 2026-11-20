# Cleaning up duplicates

## How StarMap finds copies

Two files count as copies when they have the same name, the same size and matching samples from the start and end of their contents. Files under 1 KB are ignored. Files stored only in iCloud, OneDrive or similar are never downloaded to be compared.

On the map, gold arcs join folders that share copies. The left panel shows how many files have a copy somewhere else.

## Reviewing copies

Click **Review copies** in the left panel, or the **Remove spare copies** recommendation.

- Each group shows a file name, how many copies there are, and where each copy is with its date. Click a location to fly to it.
- Copies inside code projects (folders with `package.json`, `.git`, `node_modules` and the like) are hidden at first, because removing them can break a project. Tick **Include code projects** to see them.
- Tick the copies you don't need. StarMap won't let you tick every copy in a group: at least one always stays.
- **Tick spare copies in every group** ticks all but one copy in each group, keeping the one with the shortest path.
- Your ticks are remembered in the browser until the next scan.

## Moving them to the Trash

Click **Move ticked copies to the Trash** (the Recycle Bin on Windows). The button asks you to confirm, showing how many files and how much space. Click it again within six seconds to go ahead.

For every ticked copy, StarMap first compares it **byte for byte** with the copies you're keeping. It only moves it if one of them is identical. Anything else stays where it is, and the panel says why.

Nothing is deleted outright. To get a file back, open the Trash or Recycle Bin and restore it. On macOS, **Put Back** returns it to where it was.

On macOS, the first time, you'll be asked whether Terminal may control Finder: StarMap asks Finder to move the files so that Put Back works. Click **OK**.

**Re-scan** afterwards to update the map.

**Copy list** puts the full paths of the ticked copies on the clipboard instead, if you'd rather deal with them yourself.
