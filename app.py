from flask import Flask, redirect
from db_helper import init_db, diagnose_network, get_all_scans, save_scan_result
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

init_db()

def ping_device(ip, count=5):
    result = subprocess.run(
        ["ping", "-n", str(count), "-w", "300", ip],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    latencies = [int(x) for x in re.findall(r"time[=<](\d+)ms", result.stdout)]
    loss_match = re.search(r"\((\d+)% loss\)", result.stdout)
    packet_loss = int(loss_match.group(1)) if loss_match else 100

    if not latencies:
        return None

    avg_latency = sum(latencies) / len(latencies)
    jitter = max(latencies) - min(latencies)
    return (ip, round(avg_latency), packet_loss, jitter)

@app.route("/")
def dashboard():
    diagnosis = diagnose_network()
    all_scans = get_all_scans()

    latest = {}
    for scan in all_scans:
        scan_id, ip, latency, loss, jitter, scan_time = scan
        if ip not in latest:
            latest[ip] = (latency, loss, jitter, scan_time)

    html = "<h1>🔗 وصلة - Wisla</h1>"
    html += '<a href="/scan"><button>فحص الآن 🔄</button></a>'

    html += "<h2>التشخيص:</h2><ul>"
    for line in diagnosis:
        html += f"<li>{line}</li>"
    html += "</ul>"

    html += "<h2>كل الأجهزة:</h2><ul>"
    for ip, (latency, loss, jitter, scan_time) in latest.items():
        html += f"<li>{ip} — {latency}ms | فقدان: {loss}% | تذبذب: {jitter}ms | آخر فحص: {scan_time}</li>"
    html += "</ul>"

    return html

@app.route("/scan")
def scan():
    network_prefix = "192.168.100."
    ip_list = [network_prefix + str(i) for i in range(1, 255)]

    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(ping_device, ip_list)
        for result in results:
            if result:
                ip, avg_latency, packet_loss, jitter = result
                save_scan_result(ip, avg_latency, packet_loss, jitter)

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)