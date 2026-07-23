import configparser
import ctypes
import math
import os
import struct
import sys
import time
import tkinter as tk
import tkinter.font as tkfont

# =====================================================
# CONFIG
# =====================================================
# All settings, including WATCHES, live in overlay.ini (see load_config()).

_DEFAULT_GENERAL = {
    "process_name": "FDNYFirefighter.exe",
    "refresh_ms": 33,
    "text_color": "0,255,0",  # matches the original hardcoded "lime"
    "font_size": 12,
}

def get_base_dir():
    """Directory containing the running .exe (frozen) or this script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(get_base_dir(), "overlay.ini")

def parse_int(value):
    """Parse a decimal or 0x-prefixed hex string, e.g. '40' or '0x00103A78'."""
    return int(value.strip(), 0)

def parse_rgb_to_hex(value):
    """Parse an 'R,G,B' string (each 0-255) into a Tk '#rrggbb' color."""
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 3:
        raise ValueError(f"expected 'R,G,B', got {value!r}")
    r, g, b = (int(p) for p in parts)
    for component in (r, g, b):
        if not 0 <= component <= 255:
            raise ValueError(f"RGB components must be 0-255, got {value!r}")
    return f"#{r:02x}{g:02x}{b:02x}"

def load_config(path=CONFIG_PATH):
    """Load general settings + WATCHES from overlay.ini at `path`. Falls back to
    defaults and skips bad [watch:...] sections rather than crashing.
    Returns (general_dict, watches_list, warnings_list)."""
    warnings = []
    general = dict(_DEFAULT_GENERAL)
    watches = []

    parser = configparser.ConfigParser()
    try:
        read_ok = parser.read(path)
    except configparser.Error as e:
        warnings.append(f"could not parse {os.path.basename(path)}: {e}")
        return general, watches, warnings

    if not read_ok:
        warnings.append(f"{os.path.basename(path)} not found - using built-in defaults")
        return general, watches, warnings

    if parser.has_section("general"):
        g = parser["general"]
        general["process_name"] = g.get("process_name", general["process_name"])
        general["refresh_ms"] = g.getint("refresh_ms", fallback=general["refresh_ms"])
        general["text_color"] = g.get("text_color", general["text_color"])
        general["font_size"] = g.getint("font_size", fallback=general["font_size"])

    for section in parser.sections():
        if not section.startswith("watch:"):
            continue
        label = section[len("watch:"):]
        s = parser[section]
        try:
            calculated = s.get("calculated", "").strip()
            if calculated:
                watches.append({"label": label, "module": None, "base": None, "offsets": [], "calculated": calculated})
                continue

            module = s.get("module")
            base = parse_int(s.get("base"))
            offsets_raw = s.get("offsets", "").strip()
            offsets = [parse_int(o) for o in offsets_raw.split(",") if o.strip()] if offsets_raw else []
            value_type = s.get("type", "float")
            feeds = s.get("feeds", "").strip() or None

            watches.append({
                "label": label,
                "module": module,
                "base": base,
                "offsets": offsets,
                "type": value_type,
                "feeds": feeds,
            })
        except Exception as e:
            warnings.append(f"skipped watch '{label}': {e}")

    return general, watches, warnings

CONFIG_GENERAL, WATCHES, CONFIG_WARNINGS = load_config()

PROCESS_NAME = CONFIG_GENERAL["process_name"]
REFRESH_MS = CONFIG_GENERAL["refresh_ms"]
FONT_SIZE = CONFIG_GENERAL["font_size"]

try:
    TEXT_COLOR = parse_rgb_to_hex(CONFIG_GENERAL["text_color"])
except ValueError as e:
    CONFIG_WARNINGS.append(f"invalid text_color {CONFIG_GENERAL['text_color']!r}: {e}; using default")
    TEXT_COLOR = parse_rgb_to_hex(_DEFAULT_GENERAL["text_color"])

# =====================================================
# WIN32 TYPES
# =====================================================

kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

DWORD   = ctypes.c_uint32
HANDLE  = ctypes.c_void_p
LPVOID  = ctypes.c_void_p
SIZE_T  = ctypes.c_size_t
HMODULE = ctypes.c_void_p

PTR_SIZE = ctypes.sizeof(ctypes.c_void_p)
PTR_FMT  = "Q" if PTR_SIZE == 8 else "I"

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ           = 0x0010
PROCESS_ACCESS            = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
LIST_MODULES_ALL = 0x03

# =====================================================
# STRUCTS
# =====================================================

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", DWORD),
        ("cntUsage", DWORD),
        ("th32ProcessID", DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", DWORD),
        ("cntThreads", DWORD),
        ("th32ParentProcessID", DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]

class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", LPVOID),
        ("SizeOfImage", DWORD),
        ("EntryPoint", LPVOID),
    ]

# =====================================================
# PROCESS HELPERS
# =====================================================

def get_pid(name):
    snap = kernel32.CreateToolhelp32Snapshot(0x2, 0)
    if not snap:
        return None
    pe = PROCESSENTRY32()
    pe.dwSize = ctypes.sizeof(pe)
    if not kernel32.Process32First(snap, ctypes.byref(pe)):
        kernel32.CloseHandle(snap)
        return None
    while True:
        if pe.szExeFile.decode(errors="ignore").lower() == name.lower():
            kernel32.CloseHandle(snap)
            return pe.th32ProcessID
        if not kernel32.Process32Next(snap, ctypes.byref(pe)):
            break
    kernel32.CloseHandle(snap)
    return None

def open_process(pid):
    return kernel32.OpenProcess(PROCESS_ACCESS, False, pid)

STILL_ACTIVE = 259

def is_process_alive(proc):
    """Return True if proc is a handle to a still-running process."""
    if not proc:
        return False
    exit_code = DWORD()
    if not kernel32.GetExitCodeProcess(proc, ctypes.byref(exit_code)):
        return False
    return exit_code.value == STILL_ACTIVE

def get_module_base(proc, module_name):
    hmods = (HMODULE * 1024)()
    needed = DWORD()
    if not psapi.EnumProcessModulesEx(proc, hmods, ctypes.sizeof(hmods), ctypes.byref(needed), LIST_MODULES_ALL):
        return None
    count = needed.value // ctypes.sizeof(HMODULE)
    for i in range(count):
        name_buf = ctypes.create_string_buffer(260)
        if not psapi.GetModuleBaseNameA(proc, hmods[i], name_buf, 260):
            continue
        if name_buf.value.decode(errors="ignore").lower() == module_name.lower():
            info = MODULEINFO()
            if psapi.GetModuleInformation(proc, hmods[i], ctypes.byref(info), ctypes.sizeof(info)):
                return ctypes.cast(info.lpBaseOfDll, ctypes.c_void_p).value
    return None

# =====================================================
# MEMORY READ
# =====================================================

def read_bytes(proc, addr, size):
    """Read raw bytes from process memory, or None on any failure."""
    if not addr:
        return None
    if PTR_SIZE == 4:
        addr = addr & 0xFFFFFFFF  # 32-bit game
    buf = ctypes.create_string_buffer(size)
    read = SIZE_T()
    ok = kernel32.ReadProcessMemory(proc, ctypes.c_void_p(addr), buf, size, ctypes.byref(read))
    if not ok or read.value != size:
        return None
    return buf.raw

STRUCT_FORMATS = {"float": "f", "int": "I", "byte": "B", "short": "H", "double": "d"}

def read_value(proc, addr, value_type="float"):
    """Read a typed value (float/int/byte/short/double) from process memory."""
    fmt = STRUCT_FORMATS.get(value_type.lower(), "f")
    data = read_bytes(proc, addr, struct.calcsize(fmt))
    return struct.unpack(fmt, data)[0] if data else None

def read_pointer(proc, addr):
    """Read a 32-bit pointer; null reads as None (an invalid chain step)."""
    ptr = read_value(proc, addr, "int")
    return ptr if ptr else None

def resolve_pointer_chain(proc, base_addr, offsets):
    """Follow a pointer chain, one offset at a time; None if any step fails."""
    addr = base_addr
    for offset in offsets:
        ptr = read_pointer(proc, addr)
        if ptr is None:
            return None
        addr = (ptr + offset) & 0xFFFFFFFF
    return addr

# =====================================================
# PROCESS CONNECTION STATE MACHINE
# =====================================================

class ProcessConnection:
    """
    Tracks attaching to `process_name` and automatically re-attaching if the
    process exits and is relaunched later. All OS calls are injected with
    defaults so this can be unit tested without Windows or a GUI.

    States:
      SEARCHING - no live handle; poll() looks for the process at most once
                  per search_interval.
      ATTACHED  - holds an open handle; poll() checks whether it has died.
    """

    SEARCHING = "searching"
    ATTACHED = "attached"

    def __init__(self, process_name, search_interval=1.0, max_open_attempts=5,
                 get_pid_fn=get_pid, open_process_fn=open_process,
                 is_alive_fn=is_process_alive, close_handle_fn=kernel32.CloseHandle,
                 clock=time.monotonic):
        self.process_name = process_name
        self.search_interval = search_interval
        self.max_open_attempts = max_open_attempts
        self._get_pid = get_pid_fn
        self._open_process = open_process_fn
        self._is_alive = is_alive_fn
        self._close_handle = close_handle_fn
        self._clock = clock

        self.state = self.SEARCHING
        self.pid = None
        self.proc = None
        self.attach_count = 0  # incremented on each successful attach
        self.status = f"process {process_name}\nnot found"
        self._next_search_time = 0.0  # search immediately on first poll()

    def poll(self):
        """Call on any cadence; internally throttles searching to
        search_interval and does nothing while already attached and alive."""
        if self.state == self.ATTACHED:
            if not self._is_alive(self.proc):
                self._detach()
        else:
            self._maybe_search()

    def _maybe_search(self):
        now = self._clock()
        if now < self._next_search_time:
            return
        self._next_search_time = now + self.search_interval
        self._attempt_attach()

    def _attempt_attach(self):
        pid = self._get_pid(self.process_name)
        if not pid:
            self.status = f"process {self.process_name}\nnot found"
            return

        for _ in range(self.max_open_attempts):
            proc = self._open_process(pid)
            if proc:
                self.pid = pid
                self.proc = proc
                self.state = self.ATTACHED
                self.attach_count += 1
                self.status = None
                return
        self.status = f"unable to open pid of\n{self.process_name}"

    def _detach(self):
        if self.proc:
            try:
                self._close_handle(self.proc)
            except Exception:
                pass
        self.proc = None
        self.pid = None
        self.state = self.SEARCHING
        self.status = f"process {self.process_name}\nnot found"
        self._next_search_time = 0.0  # search again immediately

    def close(self):
        """Release any held handle, e.g. on app shutdown."""
        if self.proc:
            try:
                self._close_handle(self.proc)
            except Exception:
                pass
            self.proc = None

# =====================================================
# LAYOUT
# =====================================================

WINDOW_WIDTH = 300
COLUMN_PADDING = 5
LABEL_COLUMN_FRACTION = 0.73  # rest goes to the value column
STATUS_LINES = 2  # room for the two-line "process X\nnot found" messages
LINE_PADDING = 6  # extra breathing room per row beyond the raw font metrics

# Root-window background color, never used by any real widget (every
# label/frame/button is explicitly bg="black") - see _apply_transparency.
TRANSPARENT_KEY = "#ff00fe"

# =====================================================
# GUI OVERLAY
# =====================================================

class Overlay(tk.Tk):
    def __init__(self):
        super().__init__()
        # overrideredirect() is what actually makes "borderless" reliable:
        # Tk never manages decorations for this window at all, so nothing
        # (resizable(), deiconify(), widget construction) ever has cause to
        # reassert default chrome later. Raw SetWindowLongW style-stripping
        # on a *normal* toplevel was tried instead, extensively, and kept
        # failing: Tk's own wm-level operations kept recreating the native
        # window and reverting styles our ctypes calls didn't know to
        # preserve. See _force_taskbar_icon for how the taskbar button
        # (which overrideredirect normally costs you) is recovered instead.
        self.overrideredirect(True)

        # Owns attaching/re-attaching to the game process; the overlay never
        # needs a live process to start, and recovers if the game is closed
        # and relaunched while the overlay keeps running.
        self.connection = ProcessConnection(PROCESS_NAME)
        self._attach_generation = 0  # last connection.attach_count we reset caches for

        self.title("Uncle Rick's Overlay")  # taskbar tooltip / Alt-Tab preview text
        self.attributes("-topmost", True)
        # Sets WS_EX_LAYERED, required before _apply_transparency's raw
        # SetLayeredWindowAttributes call (once hwnd is known) can combine
        # this alpha with per-pixel color-key click-through.
        self.attributes("-alpha", 0.55)
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

        # Dragging variables
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        try:
            # Tk toplevels on Windows use a wrapper-window architecture:
            # winfo_id() returns the content window, GetParent gets the
            # real outer hwnd that OS-level style/z-order calls must
            # target. update_idletasks() first, or this can return 0 - the
            # window isn't guaranteed realized yet right after __init__.
            self.update_idletasks()
            self.hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        except Exception as e:
            self.hwnd = None
            print(f"Warning: Could not get window handle: {e}")
        self._apply_transparency()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Right-click menu as a second way to close, alongside the taskbar's.
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Close", command=self.on_close)

        # Bind mouse events for dragging and the right-click menu
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)

        # Squares sized to the font itself, no padding.
        self.button_size = max(self._font.metrics("linespace"), self._font.measure("-"), self._font.measure("x"))

        # Real children of self, not a separate window: place() pins them to
        # the top-right corner and Tk keeps that true across every resize on
        # its own (recomputed on <Configure>), so there's nothing to
        # manually re-sync after a drag, a minimize/restore, or a
        # status-driven resize - the entire class of bugs where the buttons
        # drifted from the window (each fixed individually, kept recurring
        # in a new form) no longer has a mechanism to occur through.
        # Buttons stay clickable at all times (never subject to click-
        # through) because they're opaque black pixels, never the
        # TRANSPARENT_KEY color - see _apply_transparency.
        self.button_frame = tk.Frame(self, bg="black")
        self.close_btn = self._make_square_button(self.button_frame, "x", self.on_close)
        self.close_btn.pack(side="right")
        self.minimize_btn = self._make_square_button(self.button_frame, "-", self.minimize_to_taskbar)
        self.minimize_btn.pack(side="right")
        self.button_frame.place(relx=1.0, x=0, y=0, anchor="ne")

        self.status_label = tk.Label(self, fg="yellow", bg="black", font=self._font, anchor="w")
        self.status_label.bind("<Button-1>", self.start_drag)
        self.status_label.bind("<B1-Motion>", self.do_drag)
        self.status_label.bind("<ButtonRelease-1>", self.stop_drag)
        self.status_label.pack(anchor="w", fill="x")

        # Label | Value, split LABEL_COLUMN_FRACTION/rest, both left-aligned.
        # grid_propagate(False) + a fixed frame size clips anything that
        # somehow still overflows a column despite the label-text clipping
        # below, so nothing can visually spill past the window edge.
        self.watches_frame = tk.Frame(self, bg="black", width=WINDOW_WIDTH, height=self.row_height * len(WATCHES))
        self.watches_frame.pack(anchor="w")
        self.watches_frame.grid_propagate(False)
        self.watches_frame.grid_columnconfigure(0, minsize=self.label_column_width)
        self.watches_frame.grid_columnconfigure(1, minsize=self.value_column_width)

        self.items = []
        for row, w in enumerate(WATCHES):
            label_text = self._clip_text(w["label"], self.label_column_width - COLUMN_PADDING)
            label_lbl = tk.Label(self.watches_frame, text=label_text, fg=TEXT_COLOR, bg="black", font=self._font, anchor="w")
            value_lbl = tk.Label(self.watches_frame, fg=TEXT_COLOR, bg="black", font=self._font, anchor="w")
            label_lbl.grid(row=row, column=0, sticky="w", padx=(COLUMN_PADDING, 0))
            value_lbl.grid(row=row, column=1, sticky="w", padx=(0, COLUMN_PADDING))
            for widget in (label_lbl, value_lbl):
                widget.bind("<Button-1>", self.start_drag)
                widget.bind("<B1-Motion>", self.do_drag)
                widget.bind("<ButtonRelease-1>", self.stop_drag)
            self.items.append((value_lbl, w))

        # Tk stacks each newly-created sibling above the ones before it, so
        # watches_frame (created after button_frame) would otherwise paint
        # over the buttons wherever the two overlap (the top-right corner,
        # row 0) - raise button_frame above everything now that the rest of
        # the layout exists. _set_status re-raises it too, since re-packing
        # status_label later re-enters it at the top of the stack as well.
        self.button_frame.lift()

        # Cache for module bases and velocity values
        self.module_cache = {}
        self.velocity_cache = {"x": None, "y": None, "z": None}

        # Jump height tracking
        self.z_collision_center = None
        self.z_ground_height = None
        self.current_height_in_jump = 0.0  # Current height during active jump
        self.previous_jump = 0.0  # Max height of the last completed jump
        self.previous_jump_max = 0.0  # 2nd best jump height of all time
        self.current_jump_max = 0.0  # Best jump height of all time
        self.jump_baseline = None  # Baseline height at start of jump

        # Calculated-value display text, by the watch's `calculated = <kind>`
        # value in overlay.ini - not by its (freely renameable) label.
        self._calculated_text = {
            "speed": self._speed_text,
            "previous_jump": lambda: f"{self.previous_jump:.3f}",
            "previous_jump_max": lambda: f"{self.previous_jump_max:.3f}",
            "current_jump_max": lambda: f"{self.current_jump_max:.3f}",
        }
        # Where a successfully-read raw watch value also feeds other state,
        # by the watch's `feeds = <role>` value in overlay.ini.
        self._side_channels = {
            "velocity_x": lambda v: self.velocity_cache.update(x=v),
            "velocity_y": lambda v: self.velocity_cache.update(y=v),
            "velocity_z": lambda v: self.velocity_cache.update(z=v),
            "z_collision_center": lambda v: setattr(self, "z_collision_center", v),
            "player_state": lambda v: setattr(self, "player_state", v),
            "z_ground_height": lambda v: setattr(self, "z_ground_height", v),
        }

        self.after(REFRESH_MS, self.update_loop)
        self._force_taskbar_icon()

    def on_close(self):
        """Release the process handle (if any) before tearing down the window."""
        self.connection.close()
        self.destroy()

    def _make_square_button(self, parent, text, command):
        """A tight, square canvas button. A 1px outline stipple reads as
        solid or invisible depending on pixel alignment, so the border is a
        stippled frame instead: an outer TEXT_COLOR rect at 75% coverage
        (gray75 = "25% transparent"), covered by an inset solid-black rect,
        leaving only a border-width ring of dither visible. Text stays plain
        TEXT_COLOR, same as the rest of the overlay's text."""
        size = self.button_size
        border = 2
        canvas = tk.Canvas(parent, width=size, height=size, bg="black", highlightthickness=0, bd=0)
        canvas.create_rectangle(0, 0, size, size, fill=TEXT_COLOR, stipple="gray75", width=0)
        canvas.create_rectangle(border, border, size - border, size - border, fill="black", width=0)
        canvas.create_text(size // 2, size // 2, text=text, fill=TEXT_COLOR, font=self._font)

        def _on_click(event):
            command()
            return "break"  # don't also let the toplevel's drag binding fire

        canvas.bind("<Button-1>", _on_click)
        return canvas

    def minimize_to_taskbar(self):
        """Raw ShowWindow, not self.iconify(): Tcl flatly refuses
        `wm iconify` on an overrideredirect window ("override-redirect
        flag is set") - the OS call works fine regardless, Tk's own
        .state() even tracks it correctly afterward. The buttons are real
        children of this window (see __init__), so Windows minimizes and
        restores them along with it automatically - no separate window to
        withdraw/reshow, no restore-time detection needed."""
        if self.hwnd:
            SW_MINIMIZE = 6
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_MINIMIZE)

    def start_drag(self, event):
        """Start dragging the window."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True

    def do_drag(self, event):
        """Move the window while dragging. The button frame is a real
        child (see __init__) so it moves with self automatically - nothing
        else to reposition here."""
        if self.is_dragging:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            x = self.winfo_x() + dx
            y = self.winfo_y() + dy
            self.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        self.is_dragging = False

    def _apply_transparency(self):
        """Per-pixel click-through, replacing the old whole-window
        WS_EX_TRANSPARENT toggle (disabled during drag, re-enabled after -
        removed, see start_drag/stop_drag). SetLayeredWindowAttributes can
        combine LWA_COLORKEY with LWA_ALPHA in one call: pixels matching
        TRANSPARENT_KEY become fully invisible *and* pass clicks straight
        through to whatever's beneath at the OS level, while every other
        pixel (every real widget - labels, button_frame - is explicitly
        bg="black", never the key color) stays opaque, blended at the same
        alpha, and always clickable. This is also why the minimize/close
        buttons can now be plain child widgets instead of a second,
        manually-synced Toplevel: a single HWND can't selectively toggle
        WS_EX_TRANSPARENT for only part of itself, but it can decide
        click-through per pixel via the color key, which is exactly the
        "clickable controls over click-through content" split we need.
        Requires WS_EX_LAYERED, which self.attributes("-alpha", ...) in
        __init__ already sets as a side effect."""
        if not self.hwnd:
            return
        LWA_COLORKEY, LWA_ALPHA = 0x1, 0x2
        r, g, b = int(TRANSPARENT_KEY[1:3], 16), int(TRANSPARENT_KEY[3:5], 16), int(TRANSPARENT_KEY[5:7], 16)
        colorref = r | (g << 8) | (b << 16)
        alpha = round(0.55 * 255)
        try:
            ctypes.windll.user32.SetLayeredWindowAttributes(self.hwnd, colorref, alpha, LWA_COLORKEY | LWA_ALPHA)
        except Exception as e:
            print(f"Warning: Could not set layered window attributes: {e}")

    def _force_taskbar_icon(self):
        """overrideredirect() gives the window an owner, and owned windows
        are hidden from the taskbar by default. Clear the owner
        (GWLP_HWNDPARENT) and force WS_EX_APPWINDOW, then cycle visibility
        - Explorer only re-evaluates taskbar eligibility on a visibility
        transition, not on a bare style change to an already-visible
        window."""
        if not self.hwnd:
            return
        GWLP_HWNDPARENT = -8
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        SW_HIDE, SW_SHOW = 0, 5
        try:
            ctypes.windll.user32.SetWindowLongPtrW(self.hwnd, GWLP_HWNDPARENT, 0)
            ex_style = ctypes.windll.user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
            ex_style = (ex_style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style)
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_HIDE)
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_SHOW)
        except Exception as e:
            print(f"Warning: Could not force a taskbar icon: {e}")

    def get_cached_module_base(self, module_name):
        """Get module base with caching to reduce overhead."""
        if module_name not in self.module_cache:
            base = get_module_base(self.connection.proc, module_name)
            if base:
                self.module_cache[module_name] = base
            return base
        return self.module_cache[module_name]

    def status_text(self, base_text):
        """Prefix persistent config-load warnings onto a status message."""
        if CONFIG_WARNINGS and base_text:
            return " | ".join(CONFIG_WARNINGS) + " | " + base_text
        if CONFIG_WARNINGS:
            return " | ".join(CONFIG_WARNINGS)
        return base_text

    def _speed_text(self):
        vx, vy = self.velocity_cache.get("x"), self.velocity_cache.get("y")
        if vx is None or vy is None:
            return "<wait>"
        return f"{math.sqrt(vx**2 + vy**2):.3f}"  # shout out to nyddesson for the original idea on this

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
            self._set_status(self.status_text(self.connection.status or ""))
            for lbl, w in self.items:
                lbl.config(text="--")
            self.after(REFRESH_MS, self.update_loop)
            return

        # A new (re)attach happened since the last tick: cached addresses
        # from the previous process instance are no longer valid.
        if self.connection.attach_count != self._attach_generation:
            self._attach_generation = self.connection.attach_count
            self.module_cache = {}
            self.velocity_cache = {"x": None, "y": None, "z": None}
            self.z_collision_center = None
            self.z_ground_height = None
            self.jump_baseline = None

        # Nothing to say once attached - just persistent config warnings, if any.
        self._set_status(self.status_text(""))

        for lbl, w in self.items:
            label = w["label"]
            try:
                kind = w.get("calculated")
                if kind:
                    getter = self._calculated_text.get(kind)
                    lbl.config(text=getter() if getter else "<calc?>")
                    continue

                mod = self.get_cached_module_base(w["module"])
                if not mod:
                    lbl.config(text="<module?>")
                    continue

                addr = (mod + w["base"]) & 0xFFFFFFFF
                if w.get("offsets"):
                    addr = resolve_pointer_chain(self.connection.proc, addr, w["offsets"])
                    if not addr:
                        lbl.config(text="<ptr?>")
                        continue

                value_type = w.get("type", "float")
                val = read_value(self.connection.proc, addr, value_type)
                if val is None:
                    lbl.config(text="<read?>")
                    continue

                lbl.config(text=f"{val:.3f}" if value_type in ("float", "double") else f"{val}")
                side_channel = self._side_channels.get(w.get("feeds"))
                if side_channel:
                    side_channel(val)

            except Exception as e:
                lbl.config(text="<err>")
                print(f"Error reading {label}: {e}")
        
        # After reading all values, calculate jump height
        self.calculate_jump_height()
        
        self.after(REFRESH_MS, self.update_loop)
    
    def calculate_jump_height(self):
        """Update Previous/Current Jump Max from Z Collision Center vs Z
        Ground Height."""
        if self.z_collision_center is None or self.z_ground_height is None:
            return

        current_height = self.z_collision_center - self.z_ground_height
        if current_height < 50:  # crouched - not a usable baseline
            return

        if self.jump_baseline is None:
            self.jump_baseline = current_height
            self.current_height_in_jump = 0.0
            return

        relative_height = current_height - self.jump_baseline

        if abs(relative_height) < 5:  # landed
            if self.current_height_in_jump > 0:
                completed = self.current_height_in_jump
                self.previous_jump = completed
                if completed > self.current_jump_max:
                    self.previous_jump_max = self.current_jump_max
                    self.current_jump_max = completed
                elif completed > self.previous_jump_max:
                    self.previous_jump_max = completed
                self.current_height_in_jump = 0.0
            self.jump_baseline = current_height
            return

        self.current_height_in_jump = max(self.current_height_in_jump, relative_height)

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print(f"System pointer size: {PTR_SIZE} bytes")
    # Overlay owns the process connection lifecycle: it starts immediately,
    # searches for PROCESS_NAME, attaches once found, and re-attaches if the
    # game is closed and relaunched while the overlay keeps running.
    Overlay().mainloop()
