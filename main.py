import subprocess
from concurrent.futures import ThreadPoolExecutor

def ping_device(ip):
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "300", ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if result.returncode == 0:
        return ip
    return None

network_prefix = "192.168.100."
ip_list = [network_prefix + str(i) for i in range(1, 255)]

print("جاري فحص الشبكة بسرعة أكبر...")
print("-" * 40)

active_devices = []

with ThreadPoolExecutor(max_workers=50) as executor:
    results = executor.map(ping_device, ip_list)
    for ip in results:
        if ip:
            print(f"{ip} - جهاز نشط ✅")
            active_devices.append(ip)

print("-" * 40)
print(f"عدد الأجهزة النشطة: {len(active_devices)}")