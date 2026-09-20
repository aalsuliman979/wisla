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
        scan_time TEXT NOT NULL
    )
    """)
    connection.commit()
    connection.close()

def save_scan_result(ip_address, latency_ms):
    connection = get_connection()
    cursor = connection.cursor()
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO scans (ip_address, latency_ms, scan_time)
    VALUES (?, ?, ?)
    """, (ip_address, latency_ms, scan_time))
    connection.commit()
    connection.close()

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

    # نجيب آخر فحص لكل جهاز (أحدث سجل لكل IP)
    cursor.execute("""
    SELECT ip_address, latency_ms
    FROM scans
    WHERE id IN (
        SELECT MAX(id) FROM scans GROUP BY ip_address
    )
    """)
    latest_scans = cursor.fetchall()
    connection.close()

    if not latest_scans:
        return ["ما فيه بيانات كافية للتحليل بعد"]

    # نحسب المتوسط (نتجاهل القيم الفارغة)
    valid_latencies = [lat for ip, lat in latest_scans if lat is not None]
    if not valid_latencies:
        return ["ما فيه بيانات زمن استجابة صالحة"]

    average_latency = sum(valid_latencies) / len(valid_latencies)

    diagnosis = []
    diagnosis.append(f"متوسط زمن الاستجابة على شبكتك: {average_latency:.1f}ms")

    for ip, latency in latest_scans:
        if latency is None:
            continue
        if latency > average_latency * 2:
            diagnosis.append(f"🔴 جهاز {ip} بطيء جدًا ({latency}ms) — أكثر من ضعف متوسط شبكتك")
        elif latency > average_latency * 1.5:
            diagnosis.append(f"🟡 جهاز {ip} أبطأ من المعتاد ({latency}ms)")

    if len(diagnosis) == 1:
        diagnosis.append("✅ كل الأجهزة تعمل بأداء طبيعي، لا توجد مشاكل واضحة")

    return diagnosis