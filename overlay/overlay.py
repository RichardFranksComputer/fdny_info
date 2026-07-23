import configparser
import ctypes
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
    "anchor_corner": "top-left",
    "anchor_margin_x": 40,
    "anchor_margin_y": 40,
    "anchor_refresh_ms": 500,
    "text_color": "0,255,0",  # matches the original hardcoded "lime"
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

def blend_color(fg_hex, bg_hex, alpha):
    """Blend fg over bg at alpha (0-1) - fakes translucency; Tk has no real alpha."""
    fg = fg_hex.lstrip("#")
    bg = bg_hex.lstrip("#")
    fr, fg_, fb = int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16)
    br, bg_, bb = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    r = round(fr * alpha + br * (1 - alpha))
    g = round(fg_ * alpha + bg_ * (1 - alpha))
    b = round(fb * alpha + bb * (1 - alpha))
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
        general["anchor_corner"] = g.get("anchor_corner", general["anchor_corner"])
        general["anchor_margin_x"] = g.getint("anchor_margin_x", fallback=general["anchor_margin_x"])
        general["anchor_margin_y"] = g.getint("anchor_margin_y", fallback=general["anchor_margin_y"])
        general["anchor_refresh_ms"] = g.getint("anchor_refresh_ms", fallback=general["anchor_refresh_ms"])
        general["text_color"] = g.get("text_color", general["text_color"])

    for section in parser.sections():
        if not section.startswith("watch:"):
            continue
        label = section[len("watch:"):]
        s = parser[section]
        try:
            if s.getboolean("calculated", fallback=False):
                watches.append({"label": label, "module": None, "base": None, "offsets": [], "calculated": True})
                continue

            module = s.get("module")
            base = parse_int(s.get("base"))
            offsets_raw = s.get("offsets", "").strip()
            offsets = [parse_int(o) for o in offsets_raw.split(",") if o.strip()] if offsets_raw else []
            value_type = s.get("type", "float")

            watches.append({
                "label": label,
                "module": module,
                "base": base,
                "offsets": offsets,
                "type": value_type,
            })
        except Exception as e:
            warnings.append(f"skipped watch '{label}': {e}")

    return general, watches, warnings

CONFIG_GENERAL, WATCHES, CONFIG_WARNINGS = load_config()

PROCESS_NAME = CONFIG_GENERAL["process_name"]
REFRESH_MS = CONFIG_GENERAL["refresh_ms"]
ANCHOR_CORNER = CONFIG_GENERAL["anchor_corner"]
ANCHOR_MARGIN_X = CONFIG_GENERAL["anchor_margin_x"]
ANCHOR_MARGIN_Y = CONFIG_GENERAL["anchor_margin_y"]
ANCHOR_REFRESH_MS = CONFIG_GENERAL["anchor_refresh_ms"]

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
user32 = ctypes.windll.user32

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
GW_OWNER = 4

# =====================================================
# STRUCTS
# =====================================================

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

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

def get_window_rect(hwnd):
    """Return (left, top, right, bottom) screen coords for a window, or None."""
    rect = RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return (rect.left, rect.top, rect.right, rect.bottom)
    return None

def find_main_window(pid):
    """Find the top-level, visible, titled window belonging to pid with the largest area."""
    results = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd, _lparam):
        found_pid = DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(found_pid))
        if (found_pid.value == pid
                and user32.IsWindowVisible(hwnd)
                and user32.GetWindow(hwnd, GW_OWNER) == 0
                and user32.GetWindowTextLengthW(hwnd) > 0):
            results.append(hwnd)
        return True

    user32.EnumWindows(callback, 0)

    best_hwnd, best_area = None, -1
    for hwnd in results:
        rect = get_window_rect(hwnd)
        if not rect:
            continue
        area = (rect[2] - rect[0]) * (rect[3] - rect[1])
        if area > best_area:
            best_hwnd, best_area = hwnd, area
    return best_hwnd

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
    """Read bytes from process memory at given address."""
    # Ensure address is within valid range
    if addr is None or addr == 0:
        return None
    
    # For 32-bit processes, mask to 32-bit range
    if PTR_SIZE == 4:
        addr = addr & 0xFFFFFFFF
    
    buf = ctypes.create_string_buffer(size)
    read = SIZE_T()
    ok = kernel32.ReadProcessMemory(proc, ctypes.c_void_p(addr), buf, size, ctypes.byref(read))
    if not ok or read.value != size:
        return None
    return buf.raw

def read_pointer(proc, addr):
    """Read a pointer value from process memory."""
    data = read_bytes(proc, addr, 4)  # Always read 4 bytes for 32-bit game
    if not data:
        return None
    ptr = struct.unpack("I", data)[0]  # Always unpack as 32-bit unsigned int
    return ptr if ptr != 0 else None

def read_float(proc, addr):
    """Read a float value from process memory."""
    data = read_bytes(proc, addr, 4)
    return struct.unpack("f", data)[0] if data else None

def read_int(proc, addr):
    """Read a 32-bit integer from process memory."""
    data = read_bytes(proc, addr, 4)
    return struct.unpack("I", data)[0] if data else None

def read_byte(proc, addr):
    """Read a single byte from process memory."""
    data = read_bytes(proc, addr, 1)
    return struct.unpack("B", data)[0] if data else None

def read_short(proc, addr):
    """Read a 16-bit short from process memory."""
    data = read_bytes(proc, addr, 2)
    return struct.unpack("H", data)[0] if data else None

def read_double(proc, addr):
    """Read a double (64-bit float) from process memory."""
    data = read_bytes(proc, addr, 8)
    return struct.unpack("d", data)[0] if data else None

def read_value(proc, addr, value_type="float"):
    """Read a value from memory based on the specified type."""
    type_map = {
        "float": read_float,
        "int": read_int,
        "byte": read_byte,
        "short": read_short,
        "double": read_double,
    }
    reader = type_map.get(value_type.lower(), read_float)
    return reader(proc, addr)

def resolve_pointer_chain(proc, base_addr, offsets):
    """
    Resolves a pointer chain by following each offset.
    For 32-bit processes, reads 4-byte pointers.
    Returns the final address where the float value should be read.
    """
    if not offsets:
        return base_addr
    
    addr = base_addr
    
    # Follow the pointer chain
    for i, offset in enumerate(offsets):
        # Read the pointer at current address (4 bytes for 32-bit process)
        ptr = read_pointer(proc, addr)
        if ptr is None:
            return None
        
        # Add the offset to get the next address
        addr = ptr + offset
        
        # Keep address in 32-bit range
        addr = addr & 0xFFFFFFFF
    
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
# GUI OVERLAY
# =====================================================

class Overlay(tk.Tk):
    def __init__(self):
        super().__init__()
        # Owns attaching/re-attaching to the game process; the overlay never
        # needs a live process to start, and recovers if the game is closed
        # and relaunched while the overlay keeps running.
        self.connection = ProcessConnection(PROCESS_NAME)
        self._attach_generation = 0  # last connection.attach_count we reset caches for

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.55)
        self.configure(bg="black")

        # Calculate dynamic height: one status line plus one line per watch (25px each)
        num_lines = len(WATCHES) + 1
        window_height = num_lines * 25
        self._expanded_height = window_height
        self.geometry(f"300x{window_height}+40+40")

        # Dragging variables
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        # Manual offset (in pixels) accumulated from dragging, applied on top
        # of the anchor position so a drag persists across re-anchoring.
        self.anchor_dx = 0
        self.anchor_dy = 0
        self.game_hwnd = None  # looked up lazily once a pid is known

        # Click-through (will be disabled during drag)
        self.click_through_enabled = False
        self.hwnd = None
        try:
            self.hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        except Exception as e:
            print(f"Warning: Could not get window handle: {e}")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Right-click context menu, since there's no taskbar icon or title
        # bar to close the overlay from.
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Close", command=self.on_close)

        # Bind mouse events for dragging and the right-click menu
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)

        # Squares sized to the font itself, no padding.
        button_font = tkfont.Font(family="Consolas", size=12)
        self.button_size = max(button_font.metrics("linespace"), button_font.measure("-"), button_font.measure("x"))

        self.button_bar = tk.Frame(self, bg="black")
        self.button_bar.pack(fill="x")
        self.button_bar.bind("<Button-1>", self.start_drag)
        self.button_bar.bind("<B1-Motion>", self.do_drag)
        self.button_bar.bind("<ButtonRelease-1>", self.stop_drag)

        self.minimize_btn = self._make_square_button(self.button_bar, "-", self.minimize_to_taskbar)
        self.minimize_btn.pack(side="right")
        self.close_btn = self._make_square_button(self.button_bar, "x", self.on_close)
        self.close_btn.pack(side="right")

        self.status_label = tk.Label(self, fg="yellow", bg="black", font=("Consolas", 12), anchor="w")
        self.status_label.pack(anchor="w", fill="x")
        self.status_label.bind("<Button-1>", self.start_drag)
        self.status_label.bind("<B1-Motion>", self.do_drag)
        self.status_label.bind("<ButtonRelease-1>", self.stop_drag)

        self.items = []
        for w in WATCHES:
            lbl = tk.Label(self, fg=TEXT_COLOR, bg="black", font=("Consolas", 12), anchor="w")
            lbl.pack(anchor="w", fill="x")
            # Bind drag events and the right-click menu to labels too
            lbl.bind("<Button-1>", self.start_drag)
            lbl.bind("<B1-Motion>", self.do_drag)
            lbl.bind("<ButtonRelease-1>", self.stop_drag)
            self.items.append((lbl, w))

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

        self.after(REFRESH_MS, self.update_loop)
        # Position against the game window once the widget has real dimensions,
        # then keep re-syncing in case the game window moves or resizes.
        self.update_idletasks()
        self.apply_anchor()

    def on_close(self):
        """Release the process handle (if any) before tearing down the window."""
        self.connection.close()
        self.destroy()

    def _make_square_button(self, parent, text, command):
        """A tight, square canvas button. Tk has no real per-widget alpha, so
        the border uses a 50% stipple dither (Tk's actual transparency trick)
        instead of a flat blended color, which just looks like a solid shade."""
        size = self.button_size
        canvas = tk.Canvas(parent, width=size, height=size, bg="black", highlightthickness=0, bd=0)
        canvas.create_rectangle(1, 1, size - 1, size - 1, outline=TEXT_COLOR, width=1, outlinestipple="gray50")
        canvas.create_text(size // 2, size // 2, text=text, fill=TEXT_COLOR, font=("Consolas", 12))

        def _on_click(event):
            command()
            return "break"  # don't also let the toplevel's drag binding fire

        canvas.bind("<Button-1>", _on_click)
        return canvas

    def minimize_to_taskbar(self):
        """overrideredirect windows aren't WM-managed, so a real taskbar
        button (and restore) doesn't work while it's set. Drop it before
        iconifying; update_loop restores it once the window is normal again."""
        self.overrideredirect(False)
        self.iconify()

    def _restore_from_taskbar(self):
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.55)
        try:
            self.hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        except Exception as e:
            print(f"Warning: Could not get window handle after restore: {e}")

    def start_drag(self, event):
        """Start dragging the window."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True
        # Disable click-through during drag
        if self.hwnd and self.click_through_enabled:
            self.set_click_through(False)

    def do_drag(self, event):
        """Move the window while dragging, and remember the offset so it
        persists the next time the overlay re-syncs to the game window."""
        if self.is_dragging:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            self.anchor_dx += dx
            self.anchor_dy += dy
            x = self.winfo_x() + dx
            y = self.winfo_y() + dy
            self.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        """Stop dragging and re-enable click-through."""
        self.is_dragging = False
        # Re-enable click-through after drag
        if self.hwnd and not self.click_through_enabled:
            self.set_click_through(True)
    
    def set_click_through(self, enabled):
        """Enable or disable click-through."""
        if not self.hwnd:
            return
        try:
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            style = ctypes.windll.user32.GetWindowLongW(self.hwnd, -20)
            if enabled:
                ctypes.windll.user32.SetWindowLongW(self.hwnd, -20, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
                self.click_through_enabled = True
            else:
                ctypes.windll.user32.SetWindowLongW(self.hwnd, -20, style & ~WS_EX_TRANSPARENT)
                self.click_through_enabled = False
        except Exception as e:
            print(f"Warning: Could not set click-through: {e}")

    def apply_anchor(self):
        """Reposition the overlay against the configured corner of the game
        window, then reschedule itself. Skips while the user is dragging."""
        if not self.is_dragging:
            if self.game_hwnd is None or not user32.IsWindow(self.game_hwnd):
                self.game_hwnd = find_main_window(self.connection.pid)

            rect = get_window_rect(self.game_hwnd) if self.game_hwnd else None
            if rect:
                left, top, right, bottom = rect
                win_w = self.winfo_width()
                win_h = self.winfo_height()

                if ANCHOR_CORNER == "top-right":
                    x = right - win_w - ANCHOR_MARGIN_X
                    y = top + ANCHOR_MARGIN_Y
                elif ANCHOR_CORNER == "bottom-left":
                    x = left + ANCHOR_MARGIN_X
                    y = bottom - win_h - ANCHOR_MARGIN_Y
                elif ANCHOR_CORNER == "bottom-right":
                    x = right - win_w - ANCHOR_MARGIN_X
                    y = bottom - win_h - ANCHOR_MARGIN_Y
                else:  # "top-left" (default)
                    x = left + ANCHOR_MARGIN_X
                    y = top + ANCHOR_MARGIN_Y

                self.geometry(f"+{x + self.anchor_dx}+{y + self.anchor_dy}")

        self.after(ANCHOR_REFRESH_MS, self.apply_anchor)

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
        if CONFIG_WARNINGS:
            return " | ".join(CONFIG_WARNINGS) + " | " + base_text
        return base_text

    def update_loop(self):
        self.connection.poll()

        if self.connection.state != ProcessConnection.ATTACHED:
            self.status_label.config(text=self.status_text(self.connection.status or ""))
            for lbl, w in self.items:
                lbl.config(text=f"{w['label']}: --")
            self.after(REFRESH_MS, self.update_loop)
            return

        # A new (re)attach happened since the last tick: cached addresses
        # and the game window handle from the previous process instance are
        # no longer valid.
        if self.connection.attach_count != self._attach_generation:
            self._attach_generation = self.connection.attach_count
            self.module_cache = {}
            self.velocity_cache = {"x": None, "y": None, "z": None}
            self.z_collision_center = None
            self.z_ground_height = None
            self.jump_baseline = None
            self.game_hwnd = None

        self.status_label.config(text=self.status_text(f"Attached (PID {self.connection.pid})"))

        for lbl, w in self.items:
            try:
                # Handle calculated values (like Speed)
                if w.get("calculated"):
                    if w["label"] == "Speed":
                        vx = self.velocity_cache.get("x")
                        vy = self.velocity_cache.get("y")
                        if vx is not None and vy is not None:
                            import math
                            speed = math.sqrt(abs(vx)**2 + abs(vy)**2)  # shout out to nyddesson for the original idea on this
                            lbl.config(text=f"{w['label']}: {speed:.3f}")
                        else:
                            lbl.config(text=f"{w['label']}: <wait>")
                    elif w["label"] == "Previous Jump":
                        lbl.config(text=f"{w['label']}: {self.previous_jump:.3f}")
                    elif w["label"] == "Previous Jump Max":
                        lbl.config(text=f"{w['label']}: {self.previous_jump_max:.3f}")
                    elif w["label"] == "Current Jump Max":
                        lbl.config(text=f"{w['label']}: {self.current_jump_max:.3f}")
                    continue
                
                # Get module base address
                mod = self.get_cached_module_base(w["module"])
                if not mod:
                    lbl.config(text=f"{w['label']}: <module?>")
                    continue
                
                # Calculate initial address
                addr = (mod + w["base"]) & 0xFFFFFFFF
                
                # Resolve pointer chain if offsets exist
                if w.get("offsets"):
                    addr = resolve_pointer_chain(self.connection.proc, addr, w["offsets"])
                    if not addr:
                        lbl.config(text=f"{w['label']}: <ptr?>")
                        continue

                # Read the value based on its type
                value_type = w.get("type", "float")
                val = read_value(self.connection.proc, addr, value_type)
                if val is not None:
                    # Format based on type
                    if value_type in ["float", "double"]:
                        lbl.config(text=f"{w['label']}: {val:.3f}")
                    else:
                        lbl.config(text=f"{w['label']}: {val}")
                    
                    # Cache velocity values for speed calculation
                    if w["label"] == "Vel X":
                        self.velocity_cache["x"] = val
                    elif w["label"] == "Vel Y":
                        self.velocity_cache["y"] = val
                    elif w["label"] == "Vel Z":
                        self.velocity_cache["z"] = val
                    # Cache Z values for jump height calculation
                    elif w["label"] == "Z Collision Center":
                        self.z_collision_center = val
                    elif w["label"] == "Z Ground Height":
                        self.z_ground_height = val
                else:
                    lbl.config(text=f"{w['label']}: <read?>")
                    
            except Exception as e:
                lbl.config(text=f"{w['label']}: <err>")
                print(f"Error reading {w['label']}: {e}")
        
        # After reading all values, calculate jump height
        self.calculate_jump_height()
        
        self.after(REFRESH_MS, self.update_loop)
    
    def calculate_jump_height(self):
        """
        Calculate jump height by tracking the difference between Z Collision Center and Z Ground Height.
        
        Logic:
        - The difference represents the player's height above ground
        - If difference < 50, player is crouched - ignore this measurement
        - If difference >= 50, player is standing or jumping - start tracking
        
        Display values:
        - Previous Jump: Max height of the LAST completed jump (updates each jump)
        - Previous Jump Max: 2nd BEST jump height of ALL TIME (all-time leaderboard)
        - Current Jump Max: BEST jump height of ALL TIME (all-time record)
        """
        if self.z_collision_center is None or self.z_ground_height is None:
            return
        
        # Calculate current height difference (player height above ground)
        current_height = self.z_collision_center - self.z_ground_height
        
        # Ignore measurements when player is crouched (height difference < 50)
        if current_height < 50:
            return
        
        # Initialize baseline on first valid measurement (standing height >= 50)
        if self.jump_baseline is None:
            self.jump_baseline = current_height
            self.current_height_in_jump = 0.0
            return
        
        # Calculate height relative to baseline (how high above standing position)
        relative_height = current_height - self.jump_baseline
        
        # If we're back near ground (within 5 units of baseline), player has landed
        if abs(relative_height) < 5:
            # Save the completed jump's max height
            if self.current_height_in_jump > 0:
                completed_jump_max = self.current_height_in_jump
                
                # Update "Previous Jump" with this jump's max
                self.previous_jump = completed_jump_max
                
                # Update all-time leaderboard if this jump qualifies
                if completed_jump_max > self.current_jump_max:
                    # New best! Old best becomes 2nd best
                    self.previous_jump_max = self.current_jump_max
                    self.current_jump_max = completed_jump_max
                elif completed_jump_max > self.previous_jump_max:
                    # New 2nd best!
                    self.previous_jump_max = completed_jump_max
                
                # Reset for next jump
                self.current_height_in_jump = 0.0
                
            self.jump_baseline = current_height
            return
        
        # Track the maximum height during this active jump
        if relative_height > self.current_height_in_jump:
            self.current_height_in_jump = relative_height

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    print(f"System pointer size: {PTR_SIZE} bytes")
    # Overlay owns the process connection lifecycle: it starts immediately,
    # searches for PROCESS_NAME, attaches once found, and re-attaches if the
    # game is closed and relaunched while the overlay keeps running.
    Overlay().mainloop()
