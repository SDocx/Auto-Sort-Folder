"""
Auto Sort Folder — GUI
Run this file to launch the tkinter interface.
"""

import logging
import queue
import threading
import tkinter as tk
import tkinter.font
from tkinter import filedialog, scrolledtext, ttk
from pathlib import Path

import sort_downloads as sd
from watchdog.observers import Observer


# ---------------------------------------------------------------------------
# LOGGING BRIDGE — sends log records to the GUI text widget via a queue
# ---------------------------------------------------------------------------

class _QueueHandler(logging.Handler):
    """Puts formatted log records into a queue so the GUI thread can display them."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
        self.setFormatter(logging.Formatter(
            "%(asctime)s  %(message)s",
            datefmt="%H:%M:%S",
        ))

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put((record.levelname, self.format(record)))


# ---------------------------------------------------------------------------
# MAIN APPLICATION
# ---------------------------------------------------------------------------

class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Auto Sort Folder")
        self.root.geometry("780x520")
        self.root.resizable(True, True)

        self.observer: Observer | None = None
        self.log_queue: queue.Queue = queue.Queue()

        self._build_ui()
        self._attach_log_handler()
        self._poll_log_queue()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # ── Folder row ──────────────────────────────────────────────────
        folder_frame = ttk.LabelFrame(self.root, text="Watch Folder", padding=(10, 6))
        folder_frame.pack(fill="x", padx=12, pady=(12, 4))

        self.folder_var = tk.StringVar(value=str(sd.DOWNLOADS_DIR))
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var)
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.browse_btn = ttk.Button(folder_frame, text="Browse…", command=self._browse)
        self.browse_btn.pack(side="left")

        # ── Controls row ────────────────────────────────────────────────
        ctrl_frame = ttk.Frame(self.root, padding=(12, 4))
        ctrl_frame.pack(fill="x")

        self.start_btn = ttk.Button(ctrl_frame, text="▶  Start", width=12, command=self._start)
        self.start_btn.pack(side="left")

        self.stop_btn = ttk.Button(ctrl_frame, text="■  Stop", width=12, command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="Stopped")
        self.status_label = ttk.Label(ctrl_frame, textvariable=self.status_var, foreground="#888")
        self.status_label.pack(side="left", padx=4)

        clear_btn = ttk.Button(ctrl_frame, text="Clear Log", command=self._clear_log)
        clear_btn.pack(side="right")

        # ── Log area ────────────────────────────────────────────────────
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=(6, 4))
        log_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            state="disabled",
            font=("Consolas", 9) if self._font_exists("Consolas") else ("Courier", 9),
            wrap="none",
            background="#1e1e1e",
            foreground="#d4d4d4",
            insertbackground="#d4d4d4",
        )
        self.log_box.pack(fill="both", expand=True)

        # Colour tags for log levels
        self.log_box.tag_config("MOVED",        foreground="#4ec9b0")
        self.log_box.tag_config("RENAMED+MOVED", foreground="#ce9178")
        self.log_box.tag_config("DUPLICATE",    foreground="#dcdcaa")
        self.log_box.tag_config("ERROR",        foreground="#f44747")
        self.log_box.tag_config("INFO",         foreground="#d4d4d4")

    # ------------------------------------------------------------------
    # Logging bridge
    # ------------------------------------------------------------------

    def _attach_log_handler(self) -> None:
        handler = _QueueHandler(self.log_queue)
        handler.setLevel(logging.DEBUG)
        sd.log.addHandler(handler)

    def _poll_log_queue(self) -> None:
        try:
            while True:
                level, message = self.log_queue.get_nowait()
                self._append_log(level, message)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_log_queue)

    def _append_log(self, level: str, message: str) -> None:
        self.log_box.configure(state="normal")
        # Pick colour tag based on keywords in the message
        if "DUPLICATE" in message:
            tag = "DUPLICATE"
        elif "RENAMED" in message:
            tag = "RENAMED+MOVED"
        elif "MOVED" in message:
            tag = "MOVED"
        elif level == "ERROR":
            tag = "ERROR"
        else:
            tag = "INFO"
        self.log_box.insert("end", message + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _browse(self) -> None:
        path = filedialog.askdirectory(title="Select folder to watch")
        if path:
            self.folder_var.set(path)

    def _start(self) -> None:
        folder = self.folder_var.get().strip()
        if not folder:
            return

        # Point the sorting module at the chosen folder
        sd.DOWNLOADS_DIR = Path(folder)

        self._set_running(True)
        self.status_var.set(f"Watching  {folder}")
        self.status_label.configure(foreground="#4ec9b0")

        # Sort pre-existing files without freezing the UI
        threading.Thread(target=sd.sort_existing_files, daemon=True).start()

        # Start the watchdog observer
        self.observer = Observer()
        self.observer.schedule(sd.DownloadHandler(), folder, recursive=False)
        self.observer.start()

    def _stop(self) -> None:
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self._set_running(False)
        self.status_var.set("Stopped")
        self.status_label.configure(foreground="#888")

    def _clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _on_close(self) -> None:
        self._stop()
        self.root.destroy()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")
        self.browse_btn.configure(state="disabled" if running else "normal")

    @staticmethod
    def _font_exists(name: str) -> bool:
        try:
            tkinter.font.Font(family=name)
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
