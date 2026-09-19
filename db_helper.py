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