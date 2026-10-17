"""Finding a Windows process, reading its memory, and tracking attach/detach
over time. No GUI/config code."""

import ctypes
import struct
import time

# =====================================================
# WIN32 TYPES
# =====================================================

kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

DWORD   = ctypes.c_uint32
LPVOID  = ctypes.c_void_p
SIZE_T  = ctypes.c_size_t
HMODULE = ctypes.c_void_p

PTR_SIZE = ctypes.sizeof(ctypes.c_void_p)

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
    """Attaches to `process_name` and re-attaches if it exits and relaunches.
    OS calls are injected with defaults so this is unit-testable without
    Windows or a GUI. SEARCHING: no handle, polls at most once per
    search_interval. ATTACHED: holds a handle, checks whether it died."""

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
