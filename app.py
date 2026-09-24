from flask import Flask, jsonify
from db_helper import init_db, diagnose_network, get_all_scans, save_scan_result
import subprocess
import re
import socket
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

init_db()

VENDOR_PREFIXES = {
    "3C5AB4": "Samsung", "8C8590": "Samsung", "247189": "Samsung",
    "A483E7": "Apple", "F0D1A9": "Apple", "3C0754": "Apple", "F4F951": "Apple",
    "B827EB": "Raspberry Pi",
    "001A11": "Google", "F4F5D8": "Google",
    "00E04C": "Realtek", "50465D": "Amazon",
    "FCA13E": "Huawei", "00259C": "Cisco"
}

def get_mac_address(ip):
    try:
        result = subprocess.run(
            ["arp", "-a", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        match = re.search(r"([0-9a-f]{2}-){5}[0-9a-f]{2}", result.stdout, re.IGNORECASE)
        if match:
            return match.group(0).replace("-", "").upper()
    except Exception:
        pass
    return None

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None

def identify_device(ip):
    hostname = get_hostname(ip)
    if hostname and hostname != ip:
        return hostname

    mac = get_mac_address(ip)
    if mac:
        prefix = mac[:6]
        vendor = VENDOR_PREFIXES.get(prefix)
        if vendor:
            return f"جهاز {vendor}"

    return "جهاز غير معروف"

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

def format_insight(line):
    if line.startswith("🔴"):
        return {"status": "critical", "text": line.replace("🔴", "").strip()}
    if line.startswith("🟡"):
        return {"status": "warning", "text": line.replace("🟡", "").strip()}
    if line.startswith("✅"):
        return {"status": "good", "text": line.replace("✅", "").strip()}
    return {"status": "neutral", "text": line}

def get_dashboard_data():
    diagnosis = [format_insight(line) for line in diagnose_network()]
    all_scans = get_all_scans()

    latest = {}
    for scan_id, ip, latency, loss, jitter, scan_time in all_scans:
        if ip not in latest:
            latest[ip] = {
                "ip": ip,
                "name": identify_device(ip),
                "latency": latency,
                "loss": loss,
                "jitter": jitter
            }

    return {"diagnosis": diagnosis, "devices": list(latest.values())}

@app.route("/api/dashboard")
def api_dashboard():
    return jsonify(get_dashboard_data())

@app.route("/api/scan")
def api_scan():
    network_prefix = "192.168.100."
    ip_list = [network_prefix + str(i) for i in range(1, 255)]

    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(ping_device, ip_list)
        for result in results:
            if result:
                ip, avg_latency, packet_loss, jitter = result
                save_scan_result(ip, avg_latency, packet_loss, jitter)

    return jsonify(get_dashboard_data())

@app.route("/")
def home():
    html = """
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --navy: #1B2A4E;
            --coral: #FF6B5B;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body {
            height: 100%;
            overflow: hidden;
            background: var(--navy);
            font-family: 'Cairo', sans-serif;
            direction: rtl;
        }
        #network-canvas {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: 0;
        }
        .content {
            position: relative;
            z-index: 2;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            transition: filter 0.4s ease;
        }
        body.sheet-open .content {
            filter: blur(3px) brightness(0.6);
        }
        .logo-card {
            background: #f4f8fb;
            border-radius: 28px;
            padding: 18px 34px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.35);
            margin-bottom: 30px;
        }
        .logo-card img { width: 180px; display: block; }
        h1.tagline {
            color: white;
            font-size: clamp(24px, 4vw, 42px);
            font-weight: 800;
            margin-bottom: 12px;
            text-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        h1.tagline .highlight { color: var(--coral); }
        p.subtitle {
            color: #b8c2d6;
            font-size: 16px;
            margin-bottom: 40px;
            max-width: 480px;
        }
        .start-btn {
            background: var(--coral);
            color: white;
            border: none;
            padding: 16px 50px;
            font-size: 18px;
            font-weight: 700;
            border-radius: 50px;
            font-family: 'Cairo', sans-serif;
            cursor: pointer;
            box-shadow: 0 10px 30px rgba(255,107,91,0.35);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .start-btn:hover {
            transform: translateY(-4px) scale(1.05);
            box-shadow: 0 14px 40px rgba(255,107,91,0.45);
        }

        .overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0);
            z-index: 5;
            pointer-events: none;
            transition: background 0.4s ease;
        }
        body.sheet-open .overlay {
            background: rgba(0,0,0,0.25);
            pointer-events: auto;
        }

        .sheet {
            position: fixed;
            bottom: 0; left: 0; right: 0;
            height: 62vh;
            background: #f4f6f9;
            border-radius: 28px 28px 0 0;
            box-shadow: 0 -10px 50px rgba(0,0,0,0.4);
            z-index: 6;
            display: flex;
            flex-direction: column;
            transform: translateY(100%);
            transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
        }
        body.sheet-open .sheet {
            transform: translateY(0);
        }
        .sheet-handle {
            width: 44px; height: 5px;
            background: #d5dae3;
            border-radius: 10px;
            margin: 12px auto 4px auto;
            cursor: pointer;
        }
        .topbar {
            padding: 10px 30px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #e8ebf0;
        }
        .topbar h2 { color: var(--navy); font-size: 16px; }
        .scan-btn {
            background: var(--coral);
            color: white;
            border: none;
            padding: 9px 22px;
            border-radius: 40px;
            font-family: 'Cairo', sans-serif;
            font-weight: 700;
            font-size: 13px;
            cursor: pointer;
        }
        .scroll-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px 30px 30px;
        }
        .section {
            background: white;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 14px rgba(0,0,0,0.05);
        }
        .section h3 { margin-bottom: 12px; color: var(--navy); font-size: 14px; }
        .insight {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #fafbfc;
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 13.5px;
            color: #333;
        }
        .dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
        .dot.critical { background: #e74c3c; }
        .dot.warning { background: #f0ad4e; }
        .dot.good { background: #3fb950; }
        .dot.neutral { background: #8b949e; }
        .row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
            font-size: 13.5px;
            color: #333;
        }
        .row:last-child { border-bottom: none; }
        .loading { text-align: center; color: #999; padding: 20px; font-size: 14px; }
    </style>
    </head>
    <body>

    <canvas id="network-canvas"></canvas>

    <div class="content">
        <div class="logo-card">
            <img src="/static/logo.png" alt="وصلة">
        </div>
        <h1 class="tagline">افحص شبكتك <span class="highlight">بذكاء</span></h1>
        <p class="subtitle">وصلة تكتشف أجهزتك، تقيس أداء اتصالك، وتشخّص أي مشكلة بشبكتك خلال ثوانٍ</p>
        <button class="start-btn" onclick="openSheet()">ابدأ</button>
    </div>

    <div class="overlay" onclick="closeSheet()"></div>

    <div class="sheet">
        <div class="sheet-handle" onclick="closeSheet()"></div>
        <div class="topbar">
            <h2>لوحة تشخيص الشبكة</h2>
            <button class="scan-btn" onclick="runScan()">فحص الآن</button>
        </div>
        <div class="scroll-area" id="scrollArea">
            <div class="loading">اضغط "فحص الآن" لبدء فحص شبكتك</div>
        </div>
    </div>

    <script>
        function openSheet() {
            document.body.classList.add('sheet-open');
            loadDashboard();
        }
        function closeSheet() {
            document.body.classList.remove('sheet-open');
        }

        function renderData(data) {
            let html = '<div class="section"><h3>التشخيص</h3>';
            if (data.diagnosis.length === 0) {
                html += '<div class="loading">اضغط "فحص الآن" لبدء الفحص</div>';
            } else {
                data.diagnosis.forEach(d => {
                    html += `<div class="insight"><span class="dot ${d.status}"></span>${d.text}</div>`;
                });
            }
            html += '</div><div class="section"><h3>الأجهزة المكتشفة</h3>';
            data.devices.forEach(dev => {
                html += `<div class="row"><span>${dev.name}</span><span>${dev.latency}ms</span></div>`;
            });
            html += '</div>';
            document.getElementById('scrollArea').innerHTML = html;
        }

        function loadDashboard() {
            fetch('/api/dashboard')
                .then(res => res.json())
                .then(data => renderData(data));
        }

        function runScan() {
            document.getElementById('scrollArea').innerHTML = '<div class="loading">جاري فحص الشبكة...</div>';
            fetch('/api/scan')
                .then(res => res.json())
                .then(data => renderData(data));
        }

        const canvas = document.getElementById('network-canvas');
        const ctx = canvas.getContext('2d');
        let width, height;
        let mouse = { x: null, y: null };
        let logoPos = { x: 0, y: 0 };

        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
            logoPos = { x: width / 2, y: height * 0.38 };
        }
        resize();
        window.addEventListener('resize', resize);

        window.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });
        window.addEventListener('mouseleave', () => {
            mouse.x = null;
            mouse.y = null;
        });

        const PARTICLE_COUNT = 90;
        const CONNECT_DIST = 140;
        const MOUSE_DIST = 200;
        const LOGO_DIST = 260;

        let particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4
            });
        }

        function animate() {
            ctx.clearRect(0, 0, width, height);

            for (let p of particles) {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0 || p.x > width) p.vx *= -1;
                if (p.y < 0 || p.y > height) p.vy *= -1;

                ctx.beginPath();
                ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255,107,91,0.7)';
                ctx.fill();
            }

            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const a = particles[i], b = particles[j];
                    const dist = Math.hypot(a.x - b.x, a.y - b.y);
                    if (dist < CONNECT_DIST) {
                        const opacity = 1 - dist / CONNECT_DIST;
                        ctx.beginPath();
                        ctx.moveTo(a.x, a.y);
                        ctx.lineTo(b.x, b.y);
                        ctx.strokeStyle = `rgba(184, 194, 214, ${opacity * 0.3})`;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }
                }

                if (mouse.x !== null) {
                    const dist = Math.hypot(particles[i].x - mouse.x, particles[i].y - mouse.y);
                    if (dist < MOUSE_DIST) {
                        const opacity = 1 - dist / MOUSE_DIST;
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(mouse.x, mouse.y);
                        ctx.strokeStyle = `rgba(255, 107, 91, ${opacity * 0.8})`;
                        ctx.lineWidth = 1.5;
                        ctx.stroke();
                    }
                }

                const distToLogo = Math.hypot(particles[i].x - logoPos.x, particles[i].y - logoPos.y);
                if (distToLogo < LOGO_DIST) {
                    let strength = 1 - distToLogo / LOGO_DIST;
                    if (mouse.x !== null) {
                        const mouseDist = Math.hypot(particles[i].x - mouse.x, particles[i].y - mouse.y);
                        const proximity = Math.max(0, 1 - mouseDist / MOUSE_DIST);
                        strength = strength * (0.15 + proximity * 0.85);
                    } else {
                        strength = strength * 0.15;
                    }
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(logoPos.x, logoPos.y);
                    ctx.strokeStyle = `rgba(255, 107, 91, ${strength * 0.6})`;
                    ctx.lineWidth = 1.2;
                    ctx.stroke();
                }
            }

            requestAnimationFrame(animate);
        }
        animate();
    </script>

    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(debug=True)