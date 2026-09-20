import sqlite3
from datetime import datetime

def get_connection():
    connection = sqlite3.connect("wisla.db")
    return connection

def init_db():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address TEXT NOT NULL,
        latency_ms INTEGER,
        packet_loss INTEGER,
        jitter_ms INTEGER,
        scan_time TEXT NOT NULL
    )
    """)
    connection.commit()
    connection.close()

def save_scan_result(ip_address, latency_ms, packet_loss=0, jitter_ms=0):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO scans (ip_address, latency_ms, packet_loss, jitter_ms, scan_time)
        VALUES (?, ?, ?, ?, ?)
        """, (ip_address, latency_ms, packet_loss, jitter_ms, scan_time))
        connection.commit()
        connection.close()
    except sqlite3.Error as e:
        print(f"خطأ بحفظ {ip_address}: {e}")

def get_all_scans():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM scans ORDER BY scan_time DESC")
    rows = cursor.fetchall()
    connection.close()
    return rows

def diagnose_network():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT ip_address, latency_ms, packet_loss, jitter_ms
    FROM scans
    WHERE id IN (
        SELECT MAX(id) FROM scans GROUP BY ip_address
    )
    """)
    latest_scans = cursor.fetchall()
    connection.close()

    if not latest_scans:
        return ["ما فيه بيانات كافية للتحليل بعد"]

    valid = [(ip, lat, loss, jit) for ip, lat, loss, jit in latest_scans if lat is not None]
    if not valid:
        return ["ما فيه بيانات صالحة للتحليل"]

    avg_latency = sum(v[1] for v in valid) / len(valid)

    diagnosis = []
    diagnosis.append(f"متوسط زمن الاستجابة على شبكتك: {avg_latency:.1f}ms")
    diagnosis.append(f"عدد الأجهزة المفحوصة: {len(valid)}")

    for ip, latency, loss, jitter in valid:
        issues = []

        if loss and loss >= 50:
            issues.append(f"🔴 فقدان حزم خطير ({loss}%) — الاتصال شبه منقطع")
        elif loss and loss >= 20:
            issues.append(f"🟡 فقدان حزم ملحوظ ({loss}%)")

        if latency > avg_latency * 2:
            issues.append(f"🔴 بطء شديد ({latency}ms) — أكثر من ضعف المتوسط")
        elif latency > avg_latency * 1.5:
            issues.append(f"🟡 أبطأ من المعتاد ({latency}ms)")

        if jitter and jitter >= 150:
            issues.append(f"🟡 تذبذب عالي ({jitter}ms) — اتصال غير مستقر")

        if issues:
            diagnosis.append(f"جهاز {ip}: " + " | ".join(issues))

    if len(diagnosis) == 2:
        diagnosis.append("✅ كل الأجهزة تعمل بأداء طبيعي، لا توجد مشاكل واضحة")

    return diagnosis