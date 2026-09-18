import subprocess

def ping_device(ip):
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "300", ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

# نطاق الشبكة تبعك (غيّر أول 3 أرقام حسب شبكتك لو تغيرت)
network_prefix = "192.168.100."

print("جاري فحص الشبكة... هذا ممكن ياخذ دقيقة أو أكثر")
print("-" * 40)

active_devices = []

for i in range(1, 255):
    ip = network_prefix + str(i)
    if ping_device(ip):
        print(f"{ip} - جهاز نشط ✅")
        active_devices.append(ip)

print("-" * 40)
print(f"عدد الأجهزة النشطة: {len(active_devices)}")