import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
from db_helper import init_db, save_scan_result

def ping_device(ip):
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "300", ip],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    if result.returncode == 0:
        match = re.search(r"time[=<](\d+)ms", result.stdout)
        latency = int(match.group(1)) if match else None
        return (ip, latency)
    return None

init_db()

network_prefix = "192.168.100."
ip_list = [network_prefix + str(i) for i in range(1, 255)]

print("جاري فحص الشبكة وحفظ النتائج...")
print("-" * 50)

active_devices = []

with ThreadPoolExecutor(max_workers=50) as executor:
    results = executor.map(ping_device, ip_list)
    for result in results:
        if result:
            ip, latency = result
            print(f"{ip} - زمن الاستجابة: {latency}ms")
            save_scan_result(ip, latency)
            active_devices.append((ip, latency))

print("-" * 50)
print(f"عدد الأجهزة النشطة: {len(active_devices)}")
print("تم حفظ النتائج في قاعدة البيانات ✅")