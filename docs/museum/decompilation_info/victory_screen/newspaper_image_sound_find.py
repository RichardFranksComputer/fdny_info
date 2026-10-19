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
    try:
        kernel32.ReadProcessMemory(handle, address, ctypes.byref(buffer), 1, None)
        return buffer.value
    except:
        return None

pid = find_process("FDNYFirefighter.exe")
handle = kernel32.OpenProcess(PROCESS_VM_READ, False, pid)

print("SCANNING FOR ANY BYTE VALUE CHANGES")
print("="*70)
print("Scanning 0x00500000 to 0x00510000 (64KB)")
print("Tracking ALL bytes (not just zeros)...\n")

snapshot = {}
start_addr = 0x00500000
end_addr = 0x00510000

for addr in range(start_addr, end_addr):
    val = read_byte(handle, addr)
    if val is not None:
        snapshot[addr] = val
    
    if addr % 5000 == 0:
        print(f"Progress: {hex(addr)}...", end='\r')

print(f"\n✓ Snapshot complete: {len(snapshot)} bytes tracked")
print("\n" + "="*70)
print("NOW: Complete a level and wait for victory screen")
print("="*70)
input("Press Enter when newspaper is on screen...")

print("\nScanning for changes...")

changes = []
for addr, old_val in snapshot.items():
    new_val = read_byte(handle, addr)
    if new_val != old_val and new_val is not None:
        changes.append((addr, old_val, new_val))

# Filter for "interesting" changes (small values, likely flags/states)
interesting = [c for c in changes if c[1] < 20 and c[2] < 20]

print(f"\n✅ TOTAL CHANGES: {len(changes)}")
print(f"✅ INTERESTING CHANGES (values <20): {len(interesting)}")
print("="*70)

if interesting:
    print("\nMost likely candidates (small value changes):")
    for addr, old, new in interesting[:30]:
        arrow = "→"
        note = ""
        if old == 0 and new == 1:
            note = " ⭐ 0→1"
        elif old == 1 and new == 2:
            note = " ⭐ 1→2"
        elif old == 2 and new == 3:
            note = " ⭐ 2→3"
        
        print(f"  {hex(addr)}: {old} {arrow} {new}{note}")
    
    if len(interesting) > 30:
        print(f"  ... and {len(interesting) - 30} more")
else:
    print("\nNo small-value changes found!")
    print("Showing ALL changes instead:")
    for addr, old, new in changes[:50]:
        print(f"  {hex(addr)}: {old} → {new}")

print("\n" + "="*70)
print("Add candidates to Cheat Engine and test!")