import http.server
import socketserver
import json
import sqlite3
import os
import sys
import random
from urllib.parse import urlparse

PORT = 8091
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nps_bildirimler.db")

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
            status TEXT DEFAULT 'Kayıt Alındı',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

class NPSHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path in ("/admin", "/admin.html"):
            self.send_file("admin.html", "text/html; charset=utf-8")
        elif path == "/health":
            self.send_json({"status": "ok", "app": "kobi-musteri-memnuniyet-nps-scripti", "port": PORT})
        elif path == "/api/nps-listesi":
            self.handle_get_feedbacks()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/nps-gonder":
            self.handle_create_feedback()
        elif path == "/api/durum-guncelle":
            self.handle_update_status()
        else:
            self.send_error(404, "Endpoint not found")

    def send_file(self, filename, content_type):
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_create_feedback(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code") or f"NPS-2026-{random.randint(1000, 9999)}"

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO nps_feedbacks (
                    tracking_code, nps_score, rate_product, rate_support,
                    rate_speed, rate_value, feedback_text, customer_name,
                    customer_contact, order_ref, callback_requested,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tracking_code,
                int(data.get("nps_score", 0)),
                int(data.get("rate_product", 5)),
                int(data.get("rate_support", 5)),
                int(data.get("rate_speed", 5)),
                int(data.get("rate_value", 5)),
                data.get("feedback_text", ""),
                data.get("customer_name", "Anonim Müşteri"),
                data.get("customer_contact", ""),
                data.get("order_ref", ""),
                data.get("callback_requested", ""),
                data.get("status", "Kayıt Alındı"),
                data.get("created_at", "")
            ))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "tracking_code": tracking_code})
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

    def handle_update_status(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length)
        try:
            data = json.loads(post_data.decode("utf-8"))
            tracking_code = data.get("tracking_code")
            new_status = data.get("status")

            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("UPDATE nps_feedbacks SET status = ? WHERE tracking_code = ?", (new_status, tracking_code))
            conn.commit()
            conn.close()

            self.send_json({"status": "success", "updated": tracking_code})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=500)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", PORT))
    print(f"🚀 NPS ve Musteri Memnuniyeti Portali Baslatildi: http://localhost:{port}")
    print(f"⭐ Yonetim Paneli: http://localhost:{port}/admin")
    with socketserver.TCPServer(("", port), NPSHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu kapatildi.")
