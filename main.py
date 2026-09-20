import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
from db_helper import init_db, save_scan_result

def ping_device(ip, count=5):
    result = subprocess.run(
        ["ping", "-n", str(count), "-w", "300", ip],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

    # نستخرج كل أزمنة الاستجابة اللي نجحت
    latencies = [int(x) for x in re.findall(r"time[=<](\d+)ms", result.stdout)]

    # نستخرج نسبة الفقدان من ملخص Windows نفسه
    loss_match = re.search(r"\((\d+)% loss\)", result.stdout)
    packet_loss = int(loss_match.group(1)) if loss_match else 100

    if not latencies:
        return None

    avg_latency = sum(latencies) / len(latencies)
    jitter = max(latencies) - min(latencies)

    return (ip, round(avg_latency), packet_loss, jitter)

init_db()

network_prefix = "192.168.100."
ip_list = [network_prefix + str(i) for i in range(1, 255)]

print("جاري فحص جودة الاتصال لكل جهاز (5 محاولات لكل جهاز)...")
print("-" * 60)

with ThreadPoolExecutor(max_workers=30) as executor:
    results = executor.map(ping_device, ip_list)
    for result in results:
        if result:
            ip, avg_latency, packet_loss, jitter = result
            print(f"{ip} - متوسط: {avg_latency}ms | فقدان: {packet_loss}% | تذبذب: {jitter}ms")
            save_scan_result(ip, avg_latency, packet_loss, jitter)

print("-" * 60)
print("تم الفحص والحفظ ✅")