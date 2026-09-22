from flask import Flask
from db_helper import init_db, diagnose_network, get_all_scans

app = Flask(__name__)

init_db()

@app.route("/")
def dashboard():
    diagnosis = diagnose_network()
    all_scans = get_all_scans()

    # نجيب آخر فحص لكل جهاز بس (نفس منطق التشخيص)
    latest = {}
    for scan in all_scans:
        scan_id, ip, latency, loss, jitter, scan_time = scan
        if ip not in latest:
            latest[ip] = (latency, loss, jitter, scan_time)

    html = "<h1>🔗 وصلة - Wisla</h1>"
    html += "<h2>التشخيص:</h2><ul>"
    for line in diagnosis:
        html += f"<li>{line}</li>"
    html += "</ul>"

    html += "<h2>كل الأجهزة:</h2><ul>"
    for ip, (latency, loss, jitter, scan_time) in latest.items():
        html += f"<li>{ip} — {latency}ms | فقدان: {loss}% | تذبذب: {jitter}ms | آخر فحص: {scan_time}</li>"
    html += "</ul>"

    return html

if __name__ == "__main__":
    app.run(debug=True)
