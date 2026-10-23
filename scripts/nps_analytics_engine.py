# -*- coding: utf-8 -*-
"""
scripts/nps_analytics_engine.py
-------------------------------
Net Promoter Score (NPS) analitik hesaplama motoru,
Negatif NPS (0-6 Detractors) acil müdahale uyarısı ve
Google/Yandex Haritalar yorum yönlendirme kancası.
"""

import urllib.parse

DEFAULT_SETTINGS = {
    "company_name": "KOBİ Bilişim & Hizmet A.Ş.",
    "detractor_threshold": 6,
    "promoter_threshold": 9,
    "google_maps_url": "https://search.google.com/local/writereview?placeid=ChIJN1t_tDeuEmsRUsoyG83frY4",
    "yandex_maps_url": "https://yandex.com.tr/haritalar/org/kobi_servis/123456789/",
    "alert_whatsapp": "905551234567",
    "alert_email": "sikayet@kobisirket.com.tr"
}

def calculate_nps_metrics(feedbacks, detractor_threshold=6, promoter_threshold=9):
    """
    Tüm geri bildirimler üzerinden resmi NPS skoru ve alt kırılım analitiğini hesaplar.
    Formül: NPS = ((Tavsiye Edenler - Kötüleyenler) / Toplam Yanıt) * 100
    Aralık: -100 ile +100
    """
    total = len(feedbacks)
    if total == 0:
        return {
            "nps_score": 0,
            "total_count": 0,
            "promoters_count": 0,
            "promoters_pct": 0.0,
            "passives_count": 0,
            "passives_pct": 0.0,
            "detractors_count": 0,
            "detractors_pct": 0.0,
            "avg_product": 0.0,
            "avg_support": 0.0,
            "avg_speed": 0.0,
            "avg_value": 0.0,
            "callback_requests_count": 0
        }

    promoters = 0
    passives = 0
    detractors = 0
    callback_requests = 0

    sum_prod = 0
    sum_supp = 0
    sum_speed = 0
    sum_val = 0

    for f in feedbacks:
        score = int(f.get("nps_score", 0))
        if score >= promoter_threshold:
            promoters += 1
        elif score <= detractor_threshold:
            detractors += 1
        else:
            passives += 1

        if (f.get("callback_requested") or "").lower().startswith("evet"):
            callback_requests += 1

        sum_prod += int(f.get("rate_product", 5))
        sum_supp += int(f.get("rate_support", 5))
        sum_speed += int(f.get("rate_speed", 5))
        sum_val += int(f.get("rate_value", 5))

    nps = round(((promoters - detractors) / total) * 100)

    return {
        "nps_score": nps,
        "total_count": total,
        "promoters_count": promoters,
        "promoter_count": promoters,
        "promoters_pct": round(promoters * 100.0 / total, 1),
        "passives_count": passives,
        "passive_count": passives,
        "passives_pct": round(passives * 100.0 / total, 1),
        "detractors_count": detractors,
        "detractor_count": detractors,
        "detractors_pct": round(detractors * 100.0 / total, 1),
        "avg_product": round(sum_prod / total, 2),
        "avg_support": round(sum_supp / total, 2),
        "avg_speed": round(sum_speed / total, 2),
        "avg_value": round(sum_val / total, 2),
        "callback_requests_count": callback_requests
    }

def generate_detractor_alert(feedback, settings=None):
    """
    0-6 puan veren negatif müşteriler için acil müdahale (churn prevention)
    WhatsApp, hızlı arama (tel:...) ve e-posta uyarı paketi üretir.
    """
    cfg = settings or DEFAULT_SETTINGS
    tracking_code = feedback.get("tracking_code", "NPS-2026-0001")
    customer_name = feedback.get("customer_name") or "İsimsiz Müşteri"
    contact = feedback.get("customer_contact") or "İletişim Girilmedi"
    score = int(feedback.get("nps_score", 0))
    feedback_text = feedback.get("feedback_text") or "Metin girilmedi."
    order_ref = feedback.get("order_ref") or "Yok"
    callback = feedback.get("callback_requested") or "Belirtilmedi"

    clean_phone = "".join(filter(str.isdigit, contact))
    tel_link = f"tel:{clean_phone}" if clean_phone else ""

    # Müşteriye gönderilecek telafi WhatsApp mesajı
    client_wa_text = urllib.parse.quote(
        f"Sayın {customer_name},\n\n"
        f"{cfg.get('company_name', 'Şirketimiz')} olarak iletmiş olduğunuz {score}/10 puanlı memnuniyet değerlendirmenizi üzüntüyle inceledik.\n"
        f"Yaşadığınız olumsuz deneyimi telafi etmek ve sorununuzu derhal çözüme kavuşturmak istiyoruz.\n"
        f"Müşteri İlişkileri Direktörlüğümüz olarak sizinle en uygun zamanınızda görüşebilir miyiz?"
    )
    client_wa_link = f"https://wa.me/{clean_phone}?text={client_wa_text}" if clean_phone else ""

    # Şirket içi yetkililere gidecek acil bildirim metni
    internal_alert_msg = (
        f"🚨 ACİL NPS ŞİKAYET UYARISI ({tracking_code}) 🚨\n"
        f"Müşteri: {customer_name} ({contact})\n"
        f"NPS Skoru: {score} / 10 (Kötüleyen / Detractor)\n"
        f"Sipariş Ref: {order_ref}\n"
        f"Geri Arama Talebi: {callback}\n"
        f"Müşteri Şikayeti: \"{feedback_text}\"\n\n"
        f"⚠️ Müşteri kaybını önlemek için 15 dakika içinde iletişime geçilmesi tavsiye edilir."
    )

    return {
        "tracking_code": tracking_code,
        "customer_name": customer_name,
        "contact": contact,
        "score": score,
        "tel_link": tel_link,
        "client_wa_link": client_wa_link,
        "internal_alert_msg": internal_alert_msg,
        "webhook_payload": {
            "event": "nps_detractor_alert",
            "tracking_code": tracking_code,
            "score": score,
            "customer_name": customer_name,
            "contact": contact,
            "feedback": feedback_text,
            "action_required": True
        }
    }

def get_review_redirect_info(score, settings=None):
    """
    NPS puanına göre akıllı yönlendirme kararı döner.
    9-10 (Promoter) ise Google & Yandex Haritalar yorum linklerini aktif eder.
    0-6 (Detractor) ise acil şikayet modunu tetikler.
    """
    cfg = settings or DEFAULT_SETTINGS
    promoter_min = int(cfg.get("promoter_threshold", 9))
    detractor_max = int(cfg.get("detractor_threshold", 6))

    if score >= promoter_min:
        return {
            "tier": "promoter",
            "show_review_hook": True,
            "title": "🌟 Harika! Deneyiminizi Paylaşmak İster Misiniz?",
            "message": "Hizmetimizden memnun kalmanıza çok sevindik! 30 saniyenizi ayırıp Google Haritalar'da 5 yıldızlı bir yorum bırakarak ekibimize destek olmak ister misiniz?",
            "google_maps_url": cfg.get("google_maps_url", ""),
            "yandex_maps_url": cfg.get("yandex_maps_url", "")
        }
    elif score <= detractor_max:
        return {
            "tier": "detractor",
            "show_review_hook": False,
            "title": "🙏 Deneyiminizi İyileştirmek İçin Buradayız",
            "message": "Geri bildiriminiz öncelikli olarak Müşteri İlişkileri Direktörlüğümüze aktarılmıştır. Memnuniyetsizliğinizi telafi etmek adına sizinle en kısa sürede iletişime geçeceğiz.",
            "google_maps_url": "",
            "yandex_maps_url": ""
        }
    else:
        return {
            "tier": "passive",
            "show_review_hook": False,
            "title": "Teşekkür Ederiz!",
            "message": "Görüşleriniz hizmet standartlarımızı geliştirmek üzere kayıt altına alınmıştır.",
            "google_maps_url": "",
            "yandex_maps_url": ""
        }
