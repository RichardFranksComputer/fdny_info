import configparser
import ctypes
import os
import re
import tkinter as tk
import tkinter.font as tkfont

from process_reader import ProcessConnection, PTR_SIZE
from watch_engine import (
    WATCHES,
    MODULE_WARNINGS,
    PROCESS_NAME,
    WatchEngine,
    get_base_dir,
)

ICON_PATH = os.path.join(get_base_dir(), "icon.ico")

# =====================================================
# CONFIG
# =====================================================
# overlay.ini is aesthetics/behavior only - what's shown and how it's
# calculated is a values-*.py file, loaded by watch_engine.py. Nothing in
# WatchEngine reads any of these settings, so overlay.py (their only
# consumer) parses them directly instead of routing them through the engine.

_DEFAULT_GENERAL = {
    "refresh_ms": 33,
    "text_color": "#00ff00",  # the original hardcoded "lime"
    "window_width": 300,
    "font_size": 12,
    "column_padding": 5,
    "label_column_fraction": 0.73,  # rest goes to the value column
    "line_padding": 6,  # extra breathing room per row beyond the raw font metrics
    "alpha": 0.55,  # whole-window blend, used by both the Tk and Win32 layers
}

CONFIG_PATH = os.path.join(get_base_dir(), "overlay.ini")

def parse_hex_color(value):
    """Validate a Tk '#rrggbb' hex color string."""
    value = value.strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"expected '#rrggbb', got {value!r}")
    return value

def load_config(path=CONFIG_PATH):
    """Load [general] aesthetic settings from overlay.ini at `path`. Falls
    back to defaults rather than crashing on a missing/broken file.
    Returns (general_dict, warnings_list)."""
    warnings = []
    general = dict(_DEFAULT_GENERAL)

    parser = configparser.ConfigParser()
    try:
        read_ok = parser.read(path)
    except configparser.Error as e:
        warnings.append(f"could not parse {os.path.basename(path)}: {e}")
        return general, warnings

    if not read_ok:
        warnings.append(f"{os.path.basename(path)} not found - using built-in defaults")
        return general, warnings

    if parser.has_section("general"):
        g = parser["general"]
        general["refresh_ms"] = g.getint("refresh_ms", fallback=general["refresh_ms"])
        general["text_color"] = g.get("text_color", general["text_color"])
        general["window_width"] = g.getint("window_width", fallback=general["window_width"])
        general["font_size"] = g.getint("font_size", fallback=general["font_size"])
        general["column_padding"] = g.getint("column_padding", fallback=general["column_padding"])
        general["label_column_fraction"] = g.getfloat("label_column_fraction", fallback=general["label_column_fraction"])
        general["line_padding"] = g.getint("line_padding", fallback=general["line_padding"])
        general["alpha"] = g.getfloat("alpha", fallback=general["alpha"])

    return general, warnings

CONFIG_GENERAL, CONFIG_WARNINGS = load_config()
CONFIG_WARNINGS = CONFIG_WARNINGS + MODULE_WARNINGS  # ini warnings + game-module-load warnings, shown together

REFRESH_MS = CONFIG_GENERAL["refresh_ms"]
FONT_SIZE = CONFIG_GENERAL["font_size"]
WINDOW_WIDTH = CONFIG_GENERAL["window_width"]
COLUMN_PADDING = CONFIG_GENERAL["column_padding"]
LABEL_COLUMN_FRACTION = CONFIG_GENERAL["label_column_fraction"]
LINE_PADDING = CONFIG_GENERAL["line_padding"]
ALPHA = CONFIG_GENERAL["alpha"]

try:
    TEXT_COLOR = parse_hex_color(CONFIG_GENERAL["text_color"])
except ValueError as e:
    CONFIG_WARNINGS.append(f"invalid text_color {CONFIG_GENERAL['text_color']!r}: {e}; using default")
    TEXT_COLOR = _DEFAULT_GENERAL["text_color"]

# =====================================================
# LAYOUT
# =====================================================

STATUS_LINES = 2  # room for the two-line "process X\nnot found" messages

# Root-window background color, never used by any real widget (every
# label/frame/button is explicitly bg="black") - see _apply_transparency.
TRANSPARENT_KEY = "#ff00fe"


def status_text(base_text):
    """Prefix persistent config-load warnings onto a status message."""
    return " | ".join(CONFIG_WARNINGS + ([base_text] if base_text else []))

# =====================================================
# GUI OVERLAY
# =====================================================

class Overlay(tk.Tk):
    def __init__(self):
        super().__init__()
        # Tk never manages decorations for an overrideredirect window, so
        # nothing ever reasserts chrome later (unlike style-stripping a
        # normal toplevel, which _force_taskbar_icon works around below).
        self.overrideredirect(True)

        self.connection = ProcessConnection(PROCESS_NAME)
        self._attach_generation = 0  # last connection.attach_count we reset caches for
        self._placeholders_shown = False  # values currently blanked to "--"

        self.title("Uncle Rick's Overlay")  # taskbar tooltip / Alt-Tab preview text
        self.attributes("-topmost", True)
        self.attributes("-alpha", ALPHA)  # also sets WS_EX_LAYERED, needed by _apply_transparency
        self.configure(bg=TRANSPARENT_KEY)

        self._font = tkfont.Font(family="Consolas", size=FONT_SIZE)
        self.row_height = self._font.metrics("linespace") + LINE_PADDING
        available_width = WINDOW_WIDTH - 2 * COLUMN_PADDING
        self.label_column_width = round(available_width * LABEL_COLUMN_FRACTION)
        self.value_column_width = available_width - self.label_column_width

        # Status starts visible (initial state is always "searching"); the
        # window is re-sized to drop its rows once there's nothing to show.
        window_height = self._content_height(status_visible=True)
        self.geometry(f"{WINDOW_WIDTH}x{window_height}+40+40")
        self._current_height = window_height

        try:
            # GetParent(winfo_id()) gets the real outer hwnd Win32 calls
            # need; update_idletasks() first or it can return 0 (not
            # realized yet).
            self.update_idletasks()
            self.hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        except Exception as e:
            self.hwnd = None
            print(f"Warning: Could not get window handle: {e}")
        self._apply_transparency()
        self._set_icon()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # The toplevel is in every child widget's bindtags, so these two
        # bindings make the whole window draggable - labels included - with
        # no per-widget rebinding. The buttons opt out via `return "break"`.
        self._drag_offset = (0, 0)
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)

        self.status_label = tk.Label(self, fg="yellow", bg="black", font=self._font, anchor="w")
        self.status_label.pack(anchor="w", fill="x")

        # grid_propagate(False) + a fixed size hard-clips anything that
        # overflows a column despite the label-text clipping below.
        self.watches_frame = tk.Frame(self, bg="black", width=WINDOW_WIDTH, height=self.row_height * len(WATCHES))
        self.watches_frame.pack(anchor="w")
        self.watches_frame.grid_propagate(False)
        self.watches_frame.grid_columnconfigure(0, minsize=self.label_column_width)
        self.watches_frame.grid_columnconfigure(1, minsize=self.value_column_width)

        self.value_labels = []
        for row, w in enumerate(WATCHES):
            label_text = self._clip_text(w["label"], self.label_column_width - COLUMN_PADDING)
            label_lbl = tk.Label(self.watches_frame, text=label_text, fg=TEXT_COLOR, bg="black", font=self._font, anchor="w")
            value_lbl = tk.Label(self.watches_frame, fg=TEXT_COLOR, bg="black", font=self._font, anchor="w")
            label_lbl.grid(row=row, column=0, sticky="w", padx=(COLUMN_PADDING, 0))
            value_lbl.grid(row=row, column=1, sticky="w", padx=(0, COLUMN_PADDING))
            self.value_labels.append(value_lbl)

        # Built last so Tk's default stacking (newest on top) already puts
        # it above status_label/watches_frame - no lift() needed here.
        self._build_buttons()

        self.engine = WatchEngine()

        self.after(REFRESH_MS, self.update_loop)
        self._force_taskbar_icon()

    def on_close(self):
        """Release the process handle (if any) before tearing down the window."""
        self.connection.close()
        self.destroy()

    def _build_buttons(self):
        """Minimize/close buttons, top-right corner, real children of self
        (place() keeps them pinned there). Always clickable: opaque, never
        TRANSPARENT_KEY - see _apply_transparency."""
        size = self._font.metrics("linespace")
        self.button_frame = tk.Frame(self, bg="black")
        self.close_btn = self._make_square_button(self.button_frame, "x", self.on_close, size)
        self.close_btn.pack(side="right")
        self.minimize_btn = self._make_square_button(self.button_frame, "-", self.minimize_to_taskbar, size)
        self.minimize_btn.pack(side="right")
        self.button_frame.place(relx=1.0, y=0, anchor="ne")

    def _make_square_button(self, parent, text, command, size):
        """A tight, square canvas button: a TEXT_COLOR rectangle with a
        slightly smaller black one on top leaves a 1px border."""
        border = 1
        canvas = tk.Canvas(parent, width=size, height=size, bg="black", highlightthickness=0, bd=0)
        canvas.create_rectangle(0, 0, size, size, fill=TEXT_COLOR, width=0)
        canvas.create_rectangle(border, border, size - border, size - border, fill="black", width=0)
        canvas.create_text(size // 2, size // 2, text=text, fill=TEXT_COLOR, font=self._font)

        def _on_click(event):
            command()
            return "break"  # don't also let the toplevel's drag binding fire

        canvas.bind("<Button-1>", _on_click)
        return canvas

    def minimize_to_taskbar(self):
        """Raw ShowWindow, not self.iconify(): Tcl refuses `wm iconify` on
        an overrideredirect window, but the OS call works fine."""
        if self.hwnd:
            SW_MINIMIZE = 6
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_MINIMIZE)

    def start_drag(self, event):
        """Remember where inside the window the pointer grabbed it."""
        self._drag_offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def do_drag(self, event):
        dx, dy = self._drag_offset
        self.geometry(f"+{event.x_root - dx}+{event.y_root - dy}")

    def _apply_transparency(self):
        """Per-pixel click-through: SetLayeredWindowAttributes with
        LWA_COLORKEY|LWA_ALPHA makes TRANSPARENT_KEY pixels invisible and
        click-through, while every real widget (never that color) stays
        opaque, alpha-blended, and always clickable - no per-widget
        click-through toggle needed."""
        if not self.hwnd:
            return
        LWA_COLORKEY, LWA_ALPHA = 0x1, 0x2
        r, g, b = int(TRANSPARENT_KEY[1:3], 16), int(TRANSPARENT_KEY[3:5], 16), int(TRANSPARENT_KEY[5:7], 16)
        colorref = r | (g << 8) | (b << 16)
        try:
            ctypes.windll.user32.SetLayeredWindowAttributes(self.hwnd, colorref, round(ALPHA * 255), LWA_COLORKEY | LWA_ALPHA)
        except Exception as e:
            print(f"Warning: Could not set layered window attributes: {e}")

    def _set_icon(self):
        """Not Tk's iconbitmap(): it ignores the process's real DPI scale,
        so a 150%+ display still gets a stretched 32px icon. LoadImage with
        a DPI-scaled target size picks the matching .ico frame instead."""
        if not self.hwnd or not os.path.exists(ICON_PATH):
            return
        try:
            IMAGE_ICON, LR_LOADFROMFILE = 1, 0x10
            SM_CXICON, SM_CXSMICON = 11, 49
            user32 = ctypes.windll.user32
            big_size = user32.GetSystemMetrics(SM_CXICON)
            small_size = user32.GetSystemMetrics(SM_CXSMICON)
            hicon_big = user32.LoadImageW(None, ICON_PATH, IMAGE_ICON, big_size, big_size, LR_LOADFROMFILE)
            hicon_small = user32.LoadImageW(None, ICON_PATH, IMAGE_ICON, small_size, small_size, LR_LOADFROMFILE)

            WM_SETICON, ICON_SMALL, ICON_BIG = 0x80, 0, 1
            user32.SendMessageW(self.hwnd, WM_SETICON, ICON_SMALL, hicon_small)
            user32.SendMessageW(self.hwnd, WM_SETICON, ICON_BIG, hicon_big)

            GCLP_HICON, GCLP_HICONSM = -14, -34
            user32.SetClassLongPtrW(self.hwnd, GCLP_HICONSM, hicon_small)
            user32.SetClassLongPtrW(self.hwnd, GCLP_HICON, hicon_big)
        except Exception as e:
            print(f"Warning: Could not set icon from {ICON_PATH}: {e}")

    def _force_taskbar_icon(self):
        """overrideredirect() hides the window from the taskbar by default;
        clear its owner, force WS_EX_APPWINDOW, then cycle visibility -
        Explorer only re-evaluates taskbar eligibility on that transition."""
        if not self.hwnd:
            return
        GWLP_HWNDPARENT = -8
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        SW_HIDE, SW_SHOW = 0, 5
        try:
            ctypes.windll.user32.SetWindowLongPtrW(self.hwnd, GWLP_HWNDPARENT, 0)
            ex_style = ctypes.windll.user32.GetWindowLongPtrW(self.hwnd, GWL_EXSTYLE)
            ex_style = (ex_style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongPtrW(self.hwnd, GWL_EXSTYLE, ex_style)
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_HIDE)
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_SHOW)
        except Exception as e:
            print(f"Warning: Could not force a taskbar icon: {e}")

    def _clip_text(self, text, max_width):
        """Truncate text with an ellipsis so it never exceeds max_width px."""
        if self._font.measure(text) <= max_width:
            return text
        while text and self._font.measure(text + "…") > max_width:
            text = text[:-1]
        return (text + "…") if text else "…"

    def _content_height(self, status_visible):
        lines = len(WATCHES) + (STATUS_LINES if status_visible else 0)
        return lines * self.row_height

    def _set_status(self, text):
        """Show/hide the status line and resize the window to match, so
        the window never wastes space on an empty status line."""
        showing = self.status_label.winfo_manager() == "pack"
        if text:
            self.status_label.config(text=text)
            if not showing:
                self.status_label.pack(anchor="w", fill="x", before=self.watches_frame)
                self.button_frame.lift()  # re-packing bumps it back to the top of the stack
                showing = True
        elif showing:
            self.status_label.pack_forget()
            showing = False

        height = self._content_height(showing)
        if height != self._current_height:
            self._current_height = height
            self.geometry(f"{WINDOW_WIDTH}x{height}")

    def update_loop(self):
        self.connection.poll()

        if self.connection.state != ProcessConnection.ATTACHED:
            self._set_status(status_text(self.connection.status or ""))
            if not self._placeholders_shown:
                self._placeholders_shown = True
                for lbl in self.value_labels:
                    lbl.config(text="--")
            self.after(REFRESH_MS, self.update_loop)
            return

        if self.connection.attach_count != self._attach_generation:
            self._attach_generation = self.connection.attach_count
            self.engine.reset_for_new_attach()

        self._placeholders_shown = False
        self._set_status(status_text(""))

        # engine.update() returns (label, text) in WATCHES order - zip positionally.
        for lbl, (_label, text) in zip(self.value_labels, self.engine.update(self.connection.proc)):
            lbl.config(text=text)

        self.after(REFRESH_MS, self.update_loop)

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print(f"System pointer size: {PTR_SIZE} bytes")
    # A non-DPI-aware process gets DPI-virtualized icons/frames (blurry on
    # scaled displays); must be set before any window is created.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # Windows 7/8 fallback
        except Exception as e:
            print(f"Warning: Could not set DPI awareness: {e}")
    # Without this, Windows shows the hosting python.exe's icon on the
    # taskbar instead of ours. Must run before the window exists.
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FDNYOverlay.Overlay")
    except Exception as e:
        print(f"Warning: Could not set AppUserModelID: {e}")
    Overlay().mainloop()