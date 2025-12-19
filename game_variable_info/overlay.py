import ctypes
import struct
import time
import tkinter as tk

# =====================================================
# CONFIG
# =====================================================

PROCESS_NAME = "FDNYFirefighter.exe"
REFRESH_MS = 33  # ~30 FPS

WATCHES = [
    {"label": "Vel X", "module": "FDNYFirefighter.exe", "base": 0x00103A78, "offsets": [0x30, 0x104], "type": "float"},
    {"label": "Vel Y", "module": "FDNYFirefighter.exe", "base": 0x00103A78, "offsets": [0x30, 0xFC], "type": "float"},
    {"label": "Vel Z", "module": "FDNYFirefighter.exe", "base": 0x00103A78, "offsets": [0x30, 0x100], "type": "float"},
    {"label": "Speed", "module": None, "base": None, "offsets": [], "calculated": True},
    {"label": "Player State", "module": "FDNYFirefighter.exe", "base": 0x00103A78, "offsets": [0x30, 0x18c], "type": "byte"},
    {"label": "Player Ground State", "module": "FDNYFirefighter.exe", "base": 0x00103A78, "offsets": [0x30, 0x12c], "type": "byte"},
    {"label": "Z Collision Center", "module": "genesis.dll", "base": 0x362EE8, "offsets": [], "type": "float"},
    {"label": "Z Ground Height", "module": "FDNYFirefighter.exe", "base": 0x00103A78, "offsets": [0x30, 0x3404], "type": "float"},
    {"label": "Previous Jump", "module": None, "base": None, "offsets": [], "calculated": True},
    {"label": "Previous Jump Max", "module": None, "base": None, "offsets": [], "calculated": True},
    {"label": "Current Jump Max", "module": None, "base": None, "offsets": [], "calculated": True},
]

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
# GUI OVERLAY
# =====================================================

class Overlay(tk.Tk):
    def __init__(self, proc):
        super().__init__()
        self.proc = proc
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.55)
        self.configure(bg="black")
        
        # Calculate dynamic height based on number of watches (25px per line)
        num_lines = len(WATCHES)
        window_height = num_lines * 25
        self.geometry(f"300x{window_height}+40+40")

        # Dragging variables
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        # Click-through (will be disabled during drag)
        self.click_through_enabled = False
        self.hwnd = None
        try:
            self.hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        except Exception as e:
            print(f"Warning: Could not get window handle: {e}")

        # Bind mouse events for dragging
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)

        self.items = []
        for w in WATCHES:
            lbl = tk.Label(self, fg="lime", bg="black", font=("Consolas", 12), anchor="w")
            lbl.pack(anchor="w", fill="x")
            # Bind drag events to labels too
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
    
    def start_drag(self, event):
        """Start dragging the window."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True
        # Disable click-through during drag
        if self.hwnd and self.click_through_enabled:
            self.set_click_through(False)
    
    def do_drag(self, event):
        """Move the window while dragging."""
        if self.is_dragging:
            x = self.winfo_x() + event.x - self.drag_start_x
            y = self.winfo_y() + event.y - self.drag_start_y
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

    def get_cached_module_base(self, module_name):
        """Get module base with caching to reduce overhead."""
        if module_name not in self.module_cache:
            base = get_module_base(self.proc, module_name)
            if base:
                self.module_cache[module_name] = base
            return base
        return self.module_cache[module_name]

    def update_loop(self):
        for lbl, w in self.items:
            try:
                # Handle calculated values (like Speed)
                if w.get("calculated"):
                    if w["label"] == "Speed":
                        vx = self.velocity_cache.get("x")
                        vy = self.velocity_cache.get("y")
                        if vx is not None and vy is not None:
                            import math
                            speed = math.sqrt(abs(vx)**2 + abs(vy)**2)
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
                    addr = resolve_pointer_chain(self.proc, addr, w["offsets"])
                    if not addr:
                        lbl.config(text=f"{w['label']}: <ptr?>")
                        continue
                
                # Read the value based on its type
                value_type = w.get("type", "float")
                val = read_value(self.proc, addr, value_type)
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
    pid = get_pid(PROCESS_NAME)
    if not pid:
        print(f"Process '{PROCESS_NAME}' not found")
        time.sleep(2)
        raise SystemExit
    
    proc = open_process(pid)
    if not proc:
        print("Failed to open process")
        time.sleep(2)
        raise SystemExit
    
    try:
        print(f"Attached to process {PROCESS_NAME} (PID: {pid})")
        print(f"System pointer size: {PTR_SIZE} bytes")
        Overlay(proc).mainloop()
    finally:
        kernel32.CloseHandle(proc)