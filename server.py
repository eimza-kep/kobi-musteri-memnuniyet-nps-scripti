# -*- coding: utf-8 -*-
"""
server.py
---------
KOBİ Müşteri Memnuniyeti (NPS) ve CX Geri Bildirim Sunucusu.
Google/Yandex Haritalar Yönlendirmesi ve Negatif NPS (0-6) Acil Şikayet Uyarısı.
"""

import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse, parse_qs

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.nps_analytics_engine import (
    calculate_nps_metrics,
    generate_detractor_alert,
    get_review_redirect_info,
    DEFAULT_SETTINGS
)

PORT = int(os.environ.get("PORT", 8091))
DB_FILE = os.environ.get("DATABASE_PATH", os.path.join(ROOT_DIR, "nps_bildirimler.db"))

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nps_feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE,
            nps_score INTEGER,
            rate_product INTEGER,
            rate_support INTEGER,
            rate_speed INTEGER,
            rate_value INTEGER,
            feedback_text TEXT,
            customer_name TEXT,
            customer_contact TEXT,
            order_ref TEXT,
            callback_requested TEXT,
            resolution_note TEXT DEFAULT '',
            status TEXT DEFAULT 'Kayıt Alındı',
            created_at TEXT
        )
    """)

    # Kolon kontrolleri
    cur.execute("PRAGMA table_info(nps_feedbacks)")
    cols = [col[1] for col in cur.fetchall()]
    if "resolution_note" not in cols:
        cur.execute("ALTER TABLE nps_feedbacks ADD COLUMN resolution_note TEXT DEFAULT ''")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_nps_settings():
    settings = dict(DEFAULT_SETTINGS)
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        for key, value in cur.fetchall():
            if value:
                settings[key] = value
    return settings

def save_nps_settings(data):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        for key, val in data.items():
            cur.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(key), str(val))
            )
        conn.commit()

class NPSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path in ("/admin", "/admin.html"):
            self.send_file("admin.html", "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json({"status": "ok", "app": "kobi-musteri-memnuniyet-nps-scripti", "port": PORT})
        elif path == "/api/nps-listesi":
            self.handle_get_feedbacks()
        elif path == "/api/nps-metrikler":
            self.handle_get_metrics()
        elif path == "/api/ayarlar":
            self.send_json(get_nps_settings())
        elif path == "/api/detractor-alert":
            self.handle_detractor_alert(qs)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/nps-gonder":
            self.handle_create_feedback()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
        elif path == "/api/ayarlar":
            self.handle_save_settings()
        else:
            self.send_error(404, "Endpoint not found")

    def send_file(self, filename, content_type):
        filepath = os.path.join(ROOT_DIR, filename)
        if not os.path.exists(filepath):
            self.send_error(404, f"File {filename} not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def get_feedback_by_code(self, tracking_code):
        if not tracking_code:
            return None
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM nps_feedbacks WHERE tracking_code = ?", (tracking_code,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def handle_create_feedback(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code") or f"NPS-2026-{random.randint(1000, 9999)}"
            score = int(data.get("nps_score", 0))

            settings = get_nps_settings()
            detractor_max = int(settings.get("detractor_threshold", 6))

            status = data.get("status")
            if not status:
                if score <= detractor_max or "evet" in str(data.get("callback_requested", "")).lower():
                    status = "Acil İnceleme Bekliyor"
                else:
                    status = "Kayıt Alındı"

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO nps_feedbacks (
                    tracking_code, nps_score, rate_product, rate_support,
                    rate_speed, rate_value, feedback_text, customer_name,
                    customer_contact, order_ref, callback_requested,
                    resolution_note, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tracking_code,
                score,
                int(data.get("rate_product", 5)),
                int(data.get("rate_support", 5)),
                int(data.get("rate_speed", 5)),
                int(data.get("rate_value", 5)),
                data.get("feedback_text", ""),
                data.get("customer_name", "Anonim Müşteri"),
                data.get("customer_contact", ""),
                data.get("order_ref", ""),
                data.get("callback_requested", ""),
                data.get("resolution_note", ""),
                status,
                data.get("created_at", "")
            ))
            conn.commit()
            conn.close()

            redirect_info = get_review_redirect_info(score, settings)

            self.send_json({
                "status": "success",
                "tracking_code": tracking_code,
                "score": score,
                "redirect_info": redirect_info
            })
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_get_feedbacks(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM nps_feedbacks ORDER BY id DESC")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            self.send_json(rows)
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_get_metrics(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM nps_feedbacks")
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            settings = get_nps_settings()
            detractor_th = int(settings.get("detractor_threshold", 6))
            promoter_th = int(settings.get("promoter_threshold", 9))
            metrics = calculate_nps_metrics(rows, detractor_th, promoter_th)
            self.send_json({"status": "success", "metrics": metrics})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_detractor_alert(self, qs):
        tracking_code = qs.get("tracking_code", [""])[0]
        feedback = self.get_feedback_by_code(tracking_code)
        if not feedback:
            self.send_error(404, f"'{tracking_code}' takip kodlu bildirim bulunamadı.")
            return

        settings = get_nps_settings()
        alert_data = generate_detractor_alert(feedback, settings)
        self.send_json(alert_data)

    def handle_update_status(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code")
            new_status = data.get("status")
            res_note = data.get("resolution_note", "")

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                UPDATE nps_feedbacks
                SET status = ?, resolution_note = ?
                WHERE tracking_code = ?
            """, (new_status, res_note, tracking_code))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "updated": tracking_code})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

    def handle_save_settings(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            save_nps_settings(data)
            self.send_json({"status": "success", "message": "Ayarlar kaydedildi."})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=400)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 NPS ve Müşteri Memnuniyeti Portalı Başlatıldı: http://localhost:{port}")
    print(f"⭐ Yönetim Paneli: http://localhost:{port}/admin")
    with socketserver.TCPServer(("", port), NPSHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatıldı.")
