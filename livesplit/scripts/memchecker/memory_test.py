# quick_memory_test.py
import ctypes
import time

# Windows API setup
kernel32 = ctypes.windll.kernel32
OpenProcess = kernel32.OpenProcess
ReadProcessMemory = kernel32.ReadProcessMemory
PROCESS_VM_READ = 0x0010

def find_process_by_name(name):
    """Find process ID by name"""
    import psutil
    for proc in psutil.process_iter(['name', 'pid']):
        if name.lower() in proc.info['name'].lower():
            return proc.info['pid']
    return None

def read_int(handle, address):
    """Read 4-byte integer from address"""
    buffer = ctypes.c_int()
    bytes_read = ctypes.c_size_t()
    ReadProcessMemory(handle, address, ctypes.byref(buffer), 4, ctypes.byref(bytes_read))
    return buffer.value

def read_pointer_chain(handle, base, *offsets):
    """Follow a chain of pointers"""
    address = base
    
    # Follow all but the last offset (those are pointers)
    for offset in offsets[:-1]:
        ptr_value = read_int(handle, address + offset)
        if ptr_value == 0:
            return None
        address = ptr_value
    
    # Add final offset
    return address + offsets[-1]

def read_string(handle, address, max_length=256):
    """Read ASCII string from address"""
    buffer = ctypes.create_string_buffer(max_length)
    bytes_read = ctypes.c_size_t()
    ReadProcessMemory(handle, address, buffer, max_length, ctypes.byref(bytes_read))
    try:
        return buffer.value.decode('ascii', errors='ignore').split('\0')[0]
    except:
        return ""

# Main script
print("Looking for FDNYFirefighter.exe...")
pid = find_process_by_name("FDNYFirefighter.exe")

if not pid:
    print("Game not running!")
    exit()

# Open process
handle = OpenProcess(PROCESS_VM_READ, False, pid)
if not handle:
    print("Failed to open process!")
    exit()

print(f"Attached to process {pid}")
print("\nMonitoring game state (Ctrl+C to exit)...\n")

# Your addresses from the agent
GAME_STATE_BASE = 0x00502AB8
MAP_NAME_BASE = 0x00502AAC

try:
    while True:
        # Read game state: BASE → +0xC → +0x6F0
        state_addr = read_pointer_chain(handle, GAME_STATE_BASE, 0xC, 0x6F0)
        
        if state_addr:
            game_state = read_int(handle, state_addr)
            
            # Display with color/status
            status = "???"
            if game_state == 3:
                status = "PLAYING (START TIMER)"
            elif game_state == 2:
                status = "COMPLETE (STOP TIMER)"
            elif game_state == 0 or game_state == 1:
                status = "Menu"
            
            # Try to read map name: MAP_NAME_BASE → +0x660 → +0xC
            map_addr = read_pointer_chain(handle, MAP_NAME_BASE, 0x660, 0xC)
            map_name = ""
            if map_addr:
                map_name = read_string(handle, map_addr)
            
            if map_name:
                print(f"\r[{time.strftime('%H:%M:%S')}] State: {game_state} ({status}) | Map: {map_name}    ", end='', flush=True)
            else:
                print(f"\r[{time.strftime('%H:%M:%S')}] State: {game_state} ({status})    ", end='', flush=True)
        else:
            print("\rCouldn't read state (pointer chain failed)    ", end='', flush=True)
        
        time.sleep(0.2)  # Update 5 times per second

except KeyboardInterrupt:
    print("\n\nStopped.")