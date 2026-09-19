from db_helper import get_all_scans

scans = get_all_scans()

print("سجل الفحوصات المحفوظة:")
print("-" * 50)
for scan in scans:
    scan_id, ip, latency, scan_time = scan
    print(f"[{scan_time}] {ip} - {latency}ms")