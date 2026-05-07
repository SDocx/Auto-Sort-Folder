# Auto Sort Folder

A Python tool that watches a folder and automatically moves files into organised subfolders by type the moment they appear. Comes with both a GUI and a command-line mode.

---

## Features

- **Live folder watcher** — detects new files instantly using [watchdog](https://github.com/gorakhargosh/watchdog)
- **Sorts on startup** — cleans up files already in the folder when the watcher starts
- **Duplicate detection** — skips files whose content is identical to one already in the destination (SHA-256 comparison), renames on name-only conflicts
- **Activity log** — every move is recorded to `moves.log` with a timestamp, source, and destination
- **GUI mode** — tkinter window with a folder picker, live colour-coded log, and Start/Stop button
- **External config** — all settings live in `config.json`, no code editing needed
- **Windows EXE** — pre-built standalone executable available from GitHub Actions (no Python required)
- **Auto-start** — PowerShell script to register the app as a Windows logon task

---

## Folder Categories

| Subfolder | Extensions |
|-----------|-----------|
| Images | `.jpg` `.jpeg` `.png` `.gif` `.bmp` `.svg` `.webp` `.ico` `.tiff` `.heic` |
| Videos | `.mp4` `.mkv` `.mov` `.avi` `.wmv` `.flv` `.webm` `.m4v` |
| Audio | `.mp3` `.wav` `.flac` `.aac` `.ogg` `.m4a` `.wma` |
| Documents | `.pdf` `.doc` `.docx` `.xls` `.xlsx` `.ppt` `.pptx` `.txt` `.rtf` `.odt` `.csv` |
| Archives | `.zip` `.rar` `.7z` `.tar` `.gz` `.bz2` `.xz` |
| Code | `.py` `.js` `.ts` `.html` `.css` `.json` `.xml` `.yaml` `.yml` `.sh` `.bat` `.java` `.cpp` `.c` `.h` `.rs` `.go` `.rb` `.php` `.sql` |
| Executables | `.exe` `.msi` `.dmg` `.pkg` `.deb` `.apk` |
| Fonts | `.ttf` `.otf` `.woff` `.woff2` |
| Ebooks | `.epub` `.mobi` `.azw` `.azw3` |
| Misc | Everything else |

---

## Requirements

- Python 3.8+
- [watchdog](https://pypi.org/project/watchdog/)

```bash
pip install watchdog
```

---

## Usage

### GUI (recommended)

```bash
python gui.py
```

- Click **Browse** to choose any folder to watch
- Click **Start** — existing files are sorted immediately, new files are sorted as they arrive
- The activity log shows every move colour-coded in real time
- Click **Stop** or close the window to shut down cleanly

### Command line

```bash
python sort_downloads.py
```

Press **Ctrl+C** to stop.

```
20:47:12  [INFO]  Watching  /mnt/c/Users/YOUR_USERNAME/Downloads
20:47:12  [INFO]  Sorting existing files ...
20:47:12  [INFO]  MOVED      /mnt/c/.../invoice.pdf       →  /mnt/c/.../Documents/invoice.pdf
20:47:12  [INFO]  DUPLICATE  photo.jpg  (identical file already in Images — skipped)
20:47:12  [INFO]  Done sorting existing files.
```

---

## Configuration

Edit `config.json` to customise everything — no touching the Python files needed.

```json
{
  "downloads_dir": "/mnt/c/Users/YOUR_USERNAME/Downloads",
  "misc_folder": "Misc",
  "categories": {
    "Images":  [".jpg", ".png", "..."],
    "Design":  [".psd", ".ai", ".fig"]
  }
}
```

| Key | Description |
|-----|-------------|
| `downloads_dir` | Full path to the folder to watch |
| `misc_folder` | Subfolder name for unrecognised file types |
| `categories` | Map of subfolder name → list of extensions |

---

## Activity Log

Every move is appended to `moves.log` next to the script:

```
2026-05-07 20:47:12  [INFO]  MOVED        /Downloads/invoice.pdf       →  /Downloads/Documents/invoice.pdf
2026-05-07 20:47:12  [INFO]  RENAMED+MOVED  /Downloads/photo.jpg       →  /Downloads/Images/photo (1).jpg
2026-05-07 20:47:12  [INFO]  DUPLICATE    photo.jpg  (identical file already in Images — skipped)
```

---

## Download as Windows EXE

Every push to `master` triggers a GitHub Actions build on a Windows runner. No Python installation required to run the output.

1. Go to the [**Actions**](../../actions) tab on GitHub
2. Open the latest **Build Windows EXE** run
3. Download **AutoSortFolder-windows** from the Artifacts section
4. Place `AutoSortFolder.exe` and `config.json` in the same folder
5. Edit `downloads_dir` in `config.json` to match your Windows username
6. Double-click the EXE to launch

### Build locally on Windows

```bat
build.bat
```

The EXE will be created at `dist\AutoSortFolder.exe`.

---

## Run at Windows Startup

Open **Windows PowerShell** (not WSL) and run once:

```powershell
cd "\\wsl$\Ubuntu\home\sdocx\Auto-Sort-Folder"
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\setup_task.ps1
```

The app will now launch automatically every time you log into Windows.

To remove it:

```powershell
Unregister-ScheduledTask -TaskName "AutoSortFolder" -Confirm:$false
```

---

## Notes

- Hidden files (names starting with `.`) are silently skipped
- The watcher does **not** recurse into subfolders, so already-sorted files are never re-processed
- Duplicate detection compares file size first, then SHA-256 hash — large files are handled efficiently
- Works on WSL with Windows paths mounted under `/mnt/c/`

---

## License

MIT
