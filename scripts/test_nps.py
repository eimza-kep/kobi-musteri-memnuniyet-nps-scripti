import unittest
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

class TestNPSSystem(unittest.TestCase):
    def setUp(self):
        server.init_db()
        self.conn = sqlite3.connect(server.DB_FILE)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute("DELETE FROM nps_feedbacks WHERE tracking_code LIKE 'NPS-TEST%'")
        self.conn.commit()

    def tearDown(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM nps_feedbacks WHERE tracking_code LIKE 'NPS-TEST%'")
        self.conn.commit()
        self.conn.close()

    def test_database_table_exists(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nps_feedbacks'")
        row = cur.fetchone()
        self.assertIsNotNone(row, "nps_feedbacks tablosu oluşturulmuş olmalıdır.")

    def test_feedback_insert_and_retrieve(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO nps_feedbacks (
                tracking_code, nps_score, rate_product, rate_support,
                rate_speed, rate_value, feedback_text, customer_name,
                customer_contact, order_ref, callback_requested,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "NPS-TEST-001",
            10,
            5,
            5,
            5,
            5,
            "Harika bir hizmet, siparişim 1 günde geldi.",
            "Eren Çelik",
            "05553332211",
            "SIP-888",
            "Hayır",
            "Kayıt Alındı",
            "2026-09-20T10:00:00Z"
        ))
        self.conn.commit()

        cur.execute("SELECT * FROM nps_feedbacks WHERE tracking_code = 'NPS-TEST-001'")
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["customer_name"], "Eren Çelik")
        self.assertEqual(record["nps_score"], 10)

    def test_feedback_status_update(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO nps_feedbacks (tracking_code, customer_name, nps_score, status)
            VALUES (?, ?, ?, ?)
        """, ("NPS-TEST-002", "Ömer Seyfettin", 4, "Acil İnceleme Bekliyor"))
        self.conn.commit()

        cur.execute("""
            UPDATE nps_feedbacks
            SET status = 'Memnuniyet Sağlandı'
            WHERE tracking_code = 'NPS-TEST-002'
        """)
        self.conn.commit()

        cur.execute("SELECT status FROM nps_feedbacks WHERE tracking_code = 'NPS-TEST-002'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "Memnuniyet Sağlandı")

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "api.php")), "api.php bulunamadı")

if __name__ == "__main__":
    unittest.main()
