# Auto Sort Folder

A lightweight Python daemon that watches your Downloads folder and automatically moves files into organised subfolders the moment they appear.

---

## How It Works

1. On startup, sorts every file already sitting in the watched folder.
2. Starts a background watcher (powered by [watchdog](https://github.com/gorakhargosh/watchdog)).
3. Whenever a new file is created or fully written, it is moved into the matching subfolder.
4. If a file with the same name already exists at the destination, a numbered suffix is appended — no files are ever overwritten.

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

```bash
python sort_downloads.py
```

The watcher runs until you press **Ctrl+C**.

```
2026-05-07 00:04:00  [INFO]  Watching  /mnt/c/Users/YOUR_USERNAME/Downloads
2026-05-07 00:04:00  [INFO]  Press Ctrl+C to stop.

2026-05-07 00:04:00  [INFO]  Sorting existing files in /mnt/c/Users/YOUR_USERNAME/Downloads ...
2026-05-07 00:04:01  [INFO]  Moved  invoice_april.pdf          →  Documents
2026-05-07 00:04:01  [INFO]  Moved  holiday_photo.jpg          →  Images
2026-05-07 00:04:01  [INFO]  Done sorting existing files.
```

---

## Configuration

Open `sort_downloads.py` and edit the constants near the top of the file.

**Change the watched folder:**
```python
DOWNLOADS_DIR = Path("/mnt/c/Users/YOUR_USERNAME/Downloads")
```

**Add a new category or extension:**
```python
FILE_TYPES = {
    ...
    "Design": [".psd", ".ai", ".fig", ".xd"],   # ← add a new category
    "Images": [..., ".raw"],                      # ← or extend an existing one
}
```

Files whose extension does not match any category are placed in `Misc/`.

---

## Notes

- Hidden files (names starting with `.`) are silently skipped.
- The watcher does **not** recurse into subfolders, so already-sorted files are never re-processed.
- Works on WSL with Windows paths mounted under `/mnt/c/`.

---

## License

MIT
