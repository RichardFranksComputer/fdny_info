import psutil

print("Running game processes:")
for proc in psutil.process_iter(['name', 'pid']):
    name = proc.info['name'].lower()
    if 'fdny' in name or 'fire' in name or 'game' in name:
        print(f"  {proc.info['name']} (PID: {proc.info['pid']})")