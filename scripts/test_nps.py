# -*- coding: utf-8 -*-
"""
test_nps.py
-----------
KOBİ Müşteri Memnuniyeti (NPS & CSAT), Harita Yönlendirme,
Yazdırılabilir A4 Yönetici Raporu, CSV İhracı ve QR Davet testleri.
"""

import unittest
import os
import sys
import sqlite3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from scripts.nps_analytics_engine import (
    calculate_nps_metrics,
    calculate_csat_metrics,
    calculate_nps_trends,
    generate_detractor_alert,
    get_review_redirect_info,
    generate_nps_executive_report_html,
    generate_nps_csv_export,
    DEFAULT_SETTINGS
)
from scripts.nps_invitation_generator import (
    generate_survey_link,
    generate_invitation_templates,
    generate_survey_qr_svg
)

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

    def test_database_tables_exist(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nps_feedbacks'")
        row = cur.fetchone()
        self.assertIsNotNone(row, "nps_feedbacks tablosu oluşturulmuş olmalıdır.")

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        row_settings = cur.fetchone()
        self.assertIsNotNone(row_settings, "settings tablosu oluşturulmuş olmalıdır.")

    def test_feedback_insert_and_retrieve(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO nps_feedbacks (
                tracking_code, nps_score, rate_product, rate_support,
                rate_speed, rate_value, feedback_text, customer_name,
                customer_contact, order_ref, callback_requested,
                resolution_note, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "",
            "Kayıt Alındı",
            "2026-09-20T10:00:00Z"
        ))
        self.conn.commit()

        cur.execute("SELECT * FROM nps_feedbacks WHERE tracking_code = 'NPS-TEST-001'")
        record = cur.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["customer_name"], "Eren Çelik")
        self.assertEqual(record["nps_score"], 10)

    def test_feedback_status_and_resolution_update(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO nps_feedbacks (tracking_code, customer_name, nps_score, status, resolution_note)
            VALUES (?, ?, ?, ?, ?)
        """, ("NPS-TEST-002", "Ömer Seyfettin", 4, "Acil İnceleme Bekliyor", ""))
        self.conn.commit()

        cur.execute("""
            UPDATE nps_feedbacks
            SET status = 'Memnuniyet Sağlandı', resolution_note = 'Müşteri arandı, telafi kuponu tanımlandı.'
            WHERE tracking_code = 'NPS-TEST-002'
        """)
        self.conn.commit()

        cur.execute("SELECT status, resolution_note FROM nps_feedbacks WHERE tracking_code = 'NPS-TEST-002'")
        row = cur.fetchone()
        self.assertEqual(row["status"], "Memnuniyet Sağlandı")
        self.assertIn("telafi kuponu", row["resolution_note"])

    def test_settings_save_and_retrieve(self):
        test_settings = {
            "company_name": "Test KOBİ A.Ş.",
            "google_maps_url": "https://maps.google.com/test",
            "yandex_maps_url": "https://yandex.com.tr/maps/test",
            "detractor_threshold": 5,
            "promoter_threshold": 8,
            "alert_email": "test@kobi.com",
            "alert_phone": "05001112233",
            "webhook_url": "https://webhook.site/test"
        }
        server.save_nps_settings(test_settings)
        loaded = server.get_nps_settings()
        self.assertEqual(loaded["company_name"], "Test KOBİ A.Ş.")
        self.assertEqual(loaded["google_maps_url"], "https://maps.google.com/test")
        self.assertEqual(int(loaded["detractor_threshold"]), 5)
        self.assertEqual(int(loaded["promoter_threshold"]), 8)

    def test_nps_metrics_calculation(self):
        sample_feedbacks = [
            {"nps_score": 10, "rate_product": 5, "rate_support": 5, "rate_speed": 5, "rate_value": 5},
            {"nps_score": 9,  "rate_product": 4, "rate_support": 5, "rate_speed": 4, "rate_value": 4},
            {"nps_score": 8,  "rate_product": 4, "rate_support": 3, "rate_speed": 4, "rate_value": 3},
            {"nps_score": 4,  "rate_product": 2, "rate_support": 2, "rate_speed": 1, "rate_value": 2},
        ]
        # Total: 4, Promoters (9-10): 2 (50%), Passives (7-8): 1 (25%), Detractors (0-6): 1 (25%)
        # NPS = 50 - 25 = +25
        metrics = calculate_nps_metrics(sample_feedbacks, detractor_threshold=6, promoter_threshold=9)
        self.assertEqual(metrics["total_count"], 4)
        self.assertEqual(metrics["promoter_count"], 2)
        self.assertEqual(metrics["passive_count"], 1)
        self.assertEqual(metrics["detractor_count"], 1)
        self.assertEqual(metrics["nps_score"], 25)
        self.assertAlmostEqual(metrics["avg_product"], 3.75, places=2)

    def test_csat_metrics_calculation(self):
        sample_feedbacks = [
            {"rate_product": 5, "rate_support": 5, "rate_speed": 5, "rate_value": 5}, # 4 rating >=4
            {"rate_product": 4, "rate_support": 4, "rate_speed": 4, "rate_value": 3}, # 3 rating >=4
            {"rate_product": 2, "rate_support": 2, "rate_speed": 1, "rate_value": 2}, # 0 rating >=4
        ]
        # Total ratings: 12. Total >=4: 7. Overall CSAT: 7/12 * 100 = 58.3%
        csat = calculate_csat_metrics(sample_feedbacks)
        self.assertEqual(csat["overall_csat"], 58.3)
        self.assertEqual(csat["product_csat"], 66.7)
        self.assertEqual(csat["support_csat"], 66.7)

    def test_nps_trends_calculation(self):
        sample_feedbacks = [
            {"nps_score": 10, "created_at": "2026-08-15T12:00:00Z"},
            {"nps_score": 4,  "created_at": "2026-08-20T12:00:00Z"},
            {"nps_score": 9,  "created_at": "2026-09-01T12:00:00Z"},
            {"nps_score": 10, "created_at": "2026-09-10T12:00:00Z"}
        ]
        trends = calculate_nps_trends(sample_feedbacks)
        self.assertEqual(len(trends), 2)
        self.assertEqual(trends[0]["period"], "2026-08")
        self.assertEqual(trends[0]["nps_score"], 0) # 1 promoter, 1 detractor
        self.assertEqual(trends[1]["period"], "2026-09")
        self.assertEqual(trends[1]["nps_score"], 100) # 2 promoters, 0 detractors

    def test_detractor_alert_generator(self):
        feedback = {
            "tracking_code": "NPS-TEST-DETRACTOR",
            "customer_name": "Canan Dağdeviren",
            "customer_contact": "05441234567",
            "nps_score": 3,
            "feedback_text": "Kargom 5 gün gecikti, müşteri hizmetlerine ulaşamadım.",
            "order_ref": "SIP-9922",
            "callback_requested": "Evet, acil dönüş bekliyorum"
        }
        custom_settings = {
            "company_name": "Antigravity Lojistik",
            "alert_email": "sikayet@antigravity.com",
            "webhook_url": "https://webhook.site/sample"
        }
        alert = generate_detractor_alert(feedback, custom_settings)

        self.assertEqual(alert["tracking_code"], "NPS-TEST-DETRACTOR")
        self.assertEqual(alert["score"], 3)
        self.assertEqual(alert["tel_link"], "tel:05441234567")
        self.assertIn("wa.me/05441234567", alert["client_wa_link"])
        self.assertIn("Antigravity%20Lojistik", alert["client_wa_link"])
        self.assertIn("ACİL NPS ŞİKAYET UYARISI", alert["internal_alert_msg"])
        self.assertEqual(alert["webhook_payload"]["event"], "nps_detractor_alert")
        self.assertTrue(alert["webhook_payload"]["action_required"])

    def test_review_redirect_hook_promoter(self):
        settings = {
            "promoter_threshold": 9,
            "detractor_threshold": 6,
            "google_maps_url": "https://maps.google.com/review-my-shop",
            "yandex_maps_url": "https://yandex.com.tr/maps/my-shop"
        }
        redirect_info = get_review_redirect_info(10, settings)
        self.assertEqual(redirect_info["tier"], "promoter")
        self.assertTrue(redirect_info["show_review_hook"])
        self.assertEqual(redirect_info["google_maps_url"], "https://maps.google.com/review-my-shop")
        self.assertEqual(redirect_info["yandex_maps_url"], "https://yandex.com.tr/maps/my-shop")

    def test_review_redirect_hook_detractor(self):
        settings = {
            "promoter_threshold": 9,
            "detractor_threshold": 6
        }
        redirect_info = get_review_redirect_info(4, settings)
        self.assertEqual(redirect_info["tier"], "detractor")
        self.assertFalse(redirect_info["show_review_hook"])
        self.assertIn("İyileştirmek İçin Buradayız", redirect_info["title"])

    def test_review_redirect_hook_passive(self):
        settings = {
            "promoter_threshold": 9,
            "detractor_threshold": 6
        }
        redirect_info = get_review_redirect_info(8, settings)
        self.assertEqual(redirect_info["tier"], "passive")
        self.assertFalse(redirect_info["show_review_hook"])

    def test_executive_report_html_and_csv(self):
        sample_feedbacks = [
            {
                "tracking_code": "NPS-TEST-EX1",
                "customer_name": "Deniz Akın",
                "customer_contact": "05321112233",
                "nps_score": 10,
                "rate_product": 5, "rate_support": 5, "rate_speed": 5, "rate_value": 5,
                "feedback_text": "Muhteşem bir alışveriş deneyimiydi.",
                "order_ref": "SIP-1001",
                "status": "Kayıt Alındı",
                "created_at": "2026-10-01T10:00:00Z"
            },
            {
                "tracking_code": "NPS-TEST-EX2",
                "customer_name": "Serkan Öz",
                "customer_contact": "05332223344",
                "nps_score": 2,
                "rate_product": 2, "rate_support": 1, "rate_speed": 1, "rate_value": 2,
                "feedback_text": "Ürün kırık geldi ve müşteri temsilcisi ilgilenmedi.",
                "order_ref": "SIP-1002",
                "status": "Acil İnceleme Bekliyor",
                "created_at": "2026-10-02T11:00:00Z"
            }
        ]

        # A4 Executive HTML Rapor Testi
        html = generate_nps_executive_report_html(sample_feedbacks, {"company_name": "Örnek Teknoloji A.Ş."})
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("MÜŞTERİ DENEYİMİ (CX) & NPS PERFORMANS YÖNETİCİ RAPORU", html)
        self.assertIn("Örnek Teknoloji A.Ş.", html)
        self.assertIn("Serkan Öz", html)
        self.assertIn("Acil Müdahale & Churn Riski", html)

        # CSV Rapor Testi
        csv_text = generate_nps_csv_export(sample_feedbacks)
        self.assertTrue(csv_text.startswith("\ufeff"), "Excel uyumu için UTF-8 BOM ile başlamalıdır.")
        self.assertIn("Deniz Akın", csv_text)
        self.assertIn("Serkan Öz", csv_text)
        self.assertIn("Promoter", csv_text)
        self.assertIn("Detractor", csv_text)

    def test_invitation_generator_and_qr(self):
        link = generate_survey_link("http://localhost:8091", order_ref="SIP-9988", customer_name="Ali Veli", customer_contact="05559998877")
        self.assertIn("http://localhost:8091/?", link)
        self.assertIn("order_ref=SIP-9988", link)
        self.assertIn("name=Ali+Veli", link)

        templates = generate_invitation_templates("Ali Veli", "SIP-9988", link, "ABC A.Ş.")
        self.assertIn("Ali Veli", templates["whatsapp_text"])
        self.assertIn("SIP-9988", templates["sms_text"])
        self.assertIn(link, templates["email_body"])

        qr_svg = generate_survey_qr_svg(link, size=150)
        self.assertTrue(qr_svg.startswith("<svg"), "QR kodu geçerli bir SVG etiketi ile başlamalıdır.")
        self.assertIn('width="150"', qr_svg)

    def test_files_exist(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "index.html")), "index.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "admin.html")), "admin.html bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "server.py")), "server.py bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "nps_analytics_engine.py")), "nps_analytics_engine.py bulunamadı")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "scripts", "nps_invitation_generator.py")), "nps_invitation_generator.py bulunamadı")

if __name__ == "__main__":
    unittest.main()
