import ctypes
import psutil

kernel32 = ctypes.windll.kernel32
PROCESS_VM_READ = 0x0010

def find_process(name):
    for proc in psutil.process_iter(['name', 'pid']):
        if name.lower() in proc.info['name'].lower():
            return proc.info['pid']
    return None

def read_byte(handle, address):
    buffer = ctypes.c_ubyte()
    kernel32.ReadProcessMemory(handle, address, ctypes.byref(buffer), 1, None)
    return buffer.value

pid = find_process("FDNYFirefighter.exe")
handle = kernel32.OpenProcess(PROCESS_VM_READ, False, pid)

print("Scanning for pause flag...")
print("Make sure you're IN A MAP (not menu)\n")

# Take snapshot
snapshot = {}
for addr in range(0x00502A00, 0x00502B00):  # Scan around where agent said
    try:
        snapshot[addr] = read_byte(handle, addr)
    except:
        pass

print(f"Snapshot taken ({len(snapshot)} bytes)")
input("Now PAUSE the game (press ESC) and hit Enter...")

# Find changes
changes = []
for addr, old_val in snapshot.items():
    try:
        new_val = read_byte(handle, addr)
        if new_val != old_val:
            changes.append((addr, old_val, new_val))
    except:
        pass

if changes:
    print("\nFound changes when pausing:")
    for addr, old, new in changes:
        print(f"  {hex(addr)}: {old} → {new}")
else:
    print("\nNo changes found in that range.")
    print("Pause flag might be at a different address.")