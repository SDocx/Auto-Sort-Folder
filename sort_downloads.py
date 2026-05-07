"""
Downloads Folder Auto-Sorter
Watches your Downloads folder and moves new files into subfolders by type.

Requirements:
    pip install watchdog
"""

# --- Standard library imports ---
import hashlib
import json
import os
import platform
import sys
import time          # Used to keep the script running in a loop
import shutil        # Provides high-level file operations (move, copy)
import logging       # Prints timestamped status messages to the console
from pathlib import Path  # Object-oriented path handling (better than os.path)

# --- Third-party import ---
# watchdog detects file system events (file created, modified, deleted, etc.)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

def _app_dir() -> Path:
    """Folder next to the EXE when bundled by PyInstaller, or next to this script in dev."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

CONFIG_FILE = _app_dir() / "config.json"

_DEFAULT_CONFIG = {
    "downloads_dir": "auto",
    "misc_folder": "Misc",
    "categories": {
        "Images":      [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff", ".heic"],
        "Videos":      [".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm", ".m4v"],
        "Audio":       [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
        "Documents":   [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".odt", ".csv"],
        "Archives":    [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
        "Code":        [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".sh", ".bat", ".java", ".cpp", ".c", ".h", ".rs", ".go", ".rb", ".php", ".sql"],
        "Executables": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".apk"],
        "Fonts":       [".ttf", ".otf", ".woff", ".woff2"],
        "Ebooks":      [".epub", ".mobi", ".azw", ".azw3"],
    },
}

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(_DEFAULT_CONFIG, indent=2), encoding="utf-8")
    with CONFIG_FILE.open(encoding="utf-8") as f:
        return json.load(f)

def _resolve_downloads_dir(configured: str) -> Path:
    """
    Auto-detect the Downloads folder when configured is 'auto' or the path doesn't exist.
    Works on native Windows and WSL.
    """
    if configured != "auto":
        path = Path(configured)
        if path.exists():
            return path

    # Native Windows EXE — use the USERPROFILE environment variable
    if platform.system() == "Windows":
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            candidate = Path(userprofile) / "Downloads"
            if candidate.exists():
                return candidate

    # WSL / Linux — scan /mnt/c/Users/
    wsl_users = Path("/mnt/c/Users")
    if wsl_users.exists():
        skip = {"All Users", "Default", "Default User", "Public"}
        for entry in sorted(wsl_users.iterdir()):
            if entry.is_dir() and entry.name not in skip:
                candidate = entry / "Downloads"
                if candidate.exists():
                    return candidate

    if configured != "auto":
        return Path(configured)  # fall back — will raise a clear FileNotFoundError at runtime
    raise FileNotFoundError(
        "Could not find your Downloads folder automatically.\n"
        "Set 'downloads_dir' in config.json to the full path."
    )

_config       = load_config()
DOWNLOADS_DIR = _resolve_downloads_dir(_config["downloads_dir"])
MISC_FOLDER   = _config.get("misc_folder", "Misc")
FILE_TYPES    = _config["categories"]

# Build a reverse lookup: extension → folder name.
# e.g. {".jpg": "Images", ".mp4": "Videos", ...}
# This makes per-file lookups O(1) instead of scanning the whole dict each time.
EXT_TO_FOLDER = {
    ext: folder
    for folder, exts in FILE_TYPES.items()
    for ext in exts
}

# Log file written next to the EXE (or script in dev mode).
LOG_FILE = _app_dir() / "moves.log"

# Configure logging so every message shows date, time, and severity level.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# File handler — appends every move record to moves.log
_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
log.addHandler(_file_handler)


# ---------------------------------------------------------------------------
# SORTING LOGIC
# ---------------------------------------------------------------------------

def file_hash(path: Path, chunk: int = 65536) -> str:
    """Return the SHA-256 digest of a file, reading in chunks to handle large files."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


def is_exact_duplicate(src: Path, dst: Path) -> bool:
    """True when dst exists and has identical content to src."""
    if not dst.exists():
        return False
    if src.stat().st_size != dst.stat().st_size:
        return False
    return file_hash(src) == file_hash(dst)


def get_destination(file_path: Path) -> Path:
    """Return the target subfolder Path for a given file."""
    # .suffix gives the file extension including the dot, e.g. ".pdf"
    # .lower() makes the lookup case-insensitive (".PDF" == ".pdf")
    ext = file_path.suffix.lower()

    # Look up which category this extension belongs to; default to MISC_FOLDER
    folder_name = EXT_TO_FOLDER.get(ext, MISC_FOLDER)

    # Build the full path: Downloads / "Images" (for example)
    return DOWNLOADS_DIR / folder_name


def resolve_conflict(destination: Path) -> Path:
    """
    If a file with the same name already exists in the destination,
    append a counter to avoid overwriting it.
    e.g. report.pdf → report (1).pdf → report (2).pdf
    """
    if not destination.exists():
        return destination  # No conflict — use as-is

    stem = destination.stem        # Filename without extension: "report"
    suffix = destination.suffix    # Extension: ".pdf"
    parent = destination.parent    # Folder: Downloads/Documents

    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def sort_file(file_path: Path) -> None:
    """Move a single file into the correct subfolder."""
    # Skip hidden/system files (names starting with a dot on macOS/Linux,
    # or temporary files created by apps while writing — e.g. ".crdownload")
    if file_path.name.startswith("."):
        return

    # Skip files that are themselves one of our category subfolders
    if not file_path.is_file():
        return

    dest_folder = get_destination(file_path)

    # Create the subfolder if it doesn't already exist.
    # exist_ok=True means no error if it's already there.
    dest_folder.mkdir(parents=True, exist_ok=True)

    candidate = dest_folder / file_path.name

    if is_exact_duplicate(file_path, candidate):
        log.info("DUPLICATE  %s  (identical file already in %s — skipped)", file_path.name, dest_folder.name)
        return

    dest_file = resolve_conflict(candidate)

    try:
        # shutil.move works across drives; Path.rename() doesn't always.
        shutil.move(str(file_path), str(dest_file))
        if dest_file.name != file_path.name:
            log.info("RENAMED+MOVED  %s  →  %s  (name conflict)", file_path, dest_file)
        else:
            log.info("MOVED  %s  →  %s", file_path, dest_file)
    except PermissionError:
        # The file may still be locked (e.g. a download in progress).
        # We'll get another event when it's fully written, so just skip it.
        log.debug("Skipped (locked): %s", file_path.name)
    except Exception as exc:
        log.error("Failed to move %s: %s", file_path.name, exc)


# ---------------------------------------------------------------------------
# WATCHDOG EVENT HANDLER
# ---------------------------------------------------------------------------

class DownloadHandler(FileSystemEventHandler):
    """
    Called by watchdog whenever something changes inside DOWNLOADS_DIR.
    We only care about two events:
      • on_created  — a brand-new file appeared
      • on_modified — an existing file was updated (catches some downloaders
                      that create an empty placeholder then fill it)
    """

    def on_created(self, event):
        # event.is_directory is True when a folder is created — ignore those.
        if not event.is_directory:
            # A tiny sleep lets the OS finish writing before we try to move.
            time.sleep(1)
            sort_file(Path(event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            time.sleep(1)
            sort_file(Path(event.src_path))


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def sort_existing_files() -> None:
    """Sort all files already sitting in Downloads when the script starts."""
    log.info("Sorting existing files in %s ...", DOWNLOADS_DIR)
    for item in DOWNLOADS_DIR.iterdir():
        # iterdir() yields both files and subdirectories — skip subdirs
        if item.is_file():
            sort_file(item)
    log.info("Done sorting existing files.")


def main() -> None:
    log.info("Watching  %s", DOWNLOADS_DIR)
    log.info("Press Ctrl+C to stop.\n")

    # Sort files that are already there before we start watching
    sort_existing_files()

    # Create the event handler (our DownloadHandler class above)
    handler = DownloadHandler()

    # Observer runs a background thread that monitors the filesystem
    observer = Observer()

    # Tell the observer: watch DOWNLOADS_DIR, use our handler,
    # but don't recurse into subdirectories (recursive=False)
    # so we don't try to re-sort files we just moved.
    observer.schedule(handler, str(DOWNLOADS_DIR), recursive=False)

    # Start the background monitoring thread
    observer.start()

    try:
        # Keep the main thread alive. The observer thread does the real work.
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        # Ctrl+C pressed — shut down cleanly
        log.info("Stopping watcher...")
        observer.stop()

    # Wait for the observer thread to fully exit before quitting
    observer.join()
    log.info("Watcher stopped.")


if __name__ == "__main__":
    # Only run main() when this file is executed directly,
    # not when it's imported as a module by another script.
    main()
