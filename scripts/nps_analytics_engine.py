# -*- coding: utf-8 -*-
"""
scripts/nps_analytics_engine.py
-------------------------------
Net Promoter Score (NPS) ve CSAT analitik hesaplama motoru,
Negatif NPS (0-6 Detractors) acil müdahale uyarısı,
Google/Yandex Haritalar yönlendirme kancası,
Yazdırılabilir A4 CX Yönetici Raporu ve Excel CSV dışa aktarımı.
"""

import urllib.parse
import datetime
from xml.sax.saxutils import escape

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
            "promoter_count": 0,
            "promoters_pct": 0.0,
            "passives_count": 0,
            "passive_count": 0,
            "passives_pct": 0.0,
            "detractors_count": 0,
            "detractor_count": 0,
            "detractors_pct": 0.0,
            "avg_product": 0.0,
            "avg_support": 0.0,
            "avg_speed": 0.0,
            "avg_value": 0.0,
            "csat_score": 0.0,
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
    high_satisfaction_count = 0
    total_ratings = total * 4

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

        rp = int(f.get("rate_product", 5))
        rs = int(f.get("rate_support", 5))
        rsp = int(f.get("rate_speed", 5))
        rv = int(f.get("rate_value", 5))

        sum_prod += rp
        sum_supp += rs
        sum_speed += rsp
        sum_val += rv

        # 4 veya 5 yıldız memnun kabul edilir (CSAT standardı)
        for r in (rp, rs, rsp, rv):
            if r >= 4:
                high_satisfaction_count += 1

    nps = round(((promoters - detractors) / total) * 100)
    csat = round((high_satisfaction_count / total_ratings) * 100.0, 1) if total_ratings > 0 else 0.0

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
        "csat_score": csat,
        "callback_requests_count": callback_requests
    }

def calculate_csat_metrics(feedbacks):
    """
    Kategori bazlı ve genel Müşteri Memnuniyet Skoru (CSAT - Customer Satisfaction Score) hesaplar.
    Her kategori için 4 ve 5 yıldız verenlerin yüzdesi.
    """
    total = len(feedbacks)
    if total == 0:
        return {
            "overall_csat": 0.0,
            "product_csat": 0.0,
            "support_csat": 0.0,
            "speed_csat": 0.0,
            "value_csat": 0.0
        }

    prod_sat = sum(1 for f in feedbacks if int(f.get("rate_product", 5)) >= 4)
    supp_sat = sum(1 for f in feedbacks if int(f.get("rate_support", 5)) >= 4)
    speed_sat = sum(1 for f in feedbacks if int(f.get("rate_speed", 5)) >= 4)
    value_sat = sum(1 for f in feedbacks if int(f.get("rate_value", 5)) >= 4)

    overall = ((prod_sat + supp_sat + speed_sat + value_sat) / (total * 4.0)) * 100.0

    return {
        "overall_csat": round(overall, 1),
        "product_csat": round((prod_sat / total) * 100.0, 1),
        "support_csat": round((supp_sat / total) * 100.0, 1),
        "speed_csat": round((speed_sat / total) * 100.0, 1),
        "value_csat": round((value_sat / total) * 100.0, 1)
    }

def calculate_nps_trends(feedbacks):
    """
    Geri bildirimleri oluşturulma tarihine (YYYY-MM) göre gruplar ve dönemsel NPS trendini çıkarır.
    """
    groups = {}
    for f in feedbacks:
        created = f.get("created_at") or ""
        # YYYY-MM çıkar (örn: 2026-09 veya 2026-10)
        period = created[:7] if len(created) >= 7 and created[4] == '-' else "Genel Dönem"
        if period not in groups:
            groups[period] = []
        groups[period].append(f)

    trend_results = []
    for period in sorted(groups.keys()):
        items = groups[period]
        m = calculate_nps_metrics(items)
        trend_results.append({
            "period": period,
            "count": len(items),
            "nps_score": m["nps_score"],
            "csat_score": m["csat_score"],
            "promoters_count": m["promoter_count"],
            "detractors_count": m["detractor_count"]
        })
    return trend_results

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

def generate_nps_executive_report_html(feedbacks, settings=None):
    """
    A4 formatında yazdırılabilir ve PDF olarak saklanabilir
    Kurumsal CX (Müşteri Deneyimi) ve NPS Performans Yönetici Raporu (HTML).
    """
    cfg = settings or DEFAULT_SETTINGS
    company = cfg.get("company_name", "KOBİ İşletmesi")
    metrics = calculate_nps_metrics(feedbacks)
    csat = calculate_csat_metrics(feedbacks)
    report_date = datetime.date.today().strftime("%d.%m.%Y")

    nps = metrics["nps_score"]
    nps_color = "#16a34a" if nps >= 50 else ("#2563eb" if nps >= 0 else "#dc2626")

    # Acil İnceleme / Churn Riski Taşıyan Müşteriler (0-6 Detractors)
    detractors = [f for f in feedbacks if int(f.get("nps_score", 0)) <= int(cfg.get("detractor_threshold", 6))]
    
    detractor_rows = []
    for d in detractors[:10]: # İlk 10 acil vaka
        detractor_rows.append(f"""
        <tr>
            <td><b>{escape(str(d.get('tracking_code', '-')))}</b></td>
            <td><b>{escape(str(d.get('customer_name', 'Anonim')))}</b><br><small style="color:#64748b;">{escape(str(d.get('customer_contact', '-')))}</small></td>
            <td style="text-align: center; color: #dc2626; font-weight: 800;">{d.get('nps_score', 0)} / 10</td>
            <td><small>{escape(str(d.get('feedback_text', '-'))[:120])}...</small></td>
            <td><small>{escape(str(d.get('order_ref', '-')))}</small></td>
            <td><span style="font-size:0.75rem; padding: 2px 6px; border-radius: 4px; background: #fee2e2; color: #991b1b; font-weight: bold;">{escape(str(d.get('status', 'İncelemede')))}</span></td>
        </tr>
        """)

    detractor_tbody = "\n".join(detractor_rows) if detractor_rows else "<tr><td colspan='6' style='text-align:center; padding: 16px; color:#16a34a;'>Tebrikler! Aktif kötüleyen müşteri veya şikayet kaydı bulunmamaktadır.</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>NPS & CX Müşteri Deneyimi Yönetici Raporu - {escape(company)}</title>
<style>
  * {{ box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  body {{ background: #f8fafc; padding: 24px 16px; color: #0f172a; margin: 0; }}
  .toolbar {{ max-width: 1040px; margin: 0 auto 16px auto; display: flex; justify-content: space-between; align-items: center; background: white; padding: 12px 20px; border-radius: 8px; border: 1px solid #cbd5e1; }}
  .report-container {{ max-width: 1040px; margin: auto; background: white; border: 1px solid #cbd5e1; padding: 36px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.03); }}
  .report-header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 24px; }}
  .header-left h1 {{ margin: 0; font-size: 1.35rem; text-transform: uppercase; font-weight: 800; }}
  .header-left p {{ margin: 4px 0 0 0; color: #64748b; font-size: 0.9rem; }}
  .header-right {{ text-align: right; font-size: 0.85rem; color: #334155; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }}
  .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; border-left: 5px solid #2563eb; text-align: center; }}
  .kpi-title {{ font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 700; }}
  .kpi-value {{ font-size: 1.8rem; font-weight: 900; margin-top: 4px; }}
  .breakdown-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px; }}
  .box {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; background: #fafafa; }}
  .box-title {{ font-size: 0.9rem; font-weight: 700; margin-bottom: 12px; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}
  .segment-bar {{ display: flex; height: 24px; border-radius: 6px; overflow: hidden; margin-bottom: 12px; }}
  .seg-p {{ background: #16a34a; color: white; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; }}
  .seg-pass {{ background: #f59e0b; color: white; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; }}
  .seg-d {{ background: #dc2626; color: white; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: bold; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.84rem; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 8px 10px; text-align: left; vertical-align: middle; }}
  th {{ background: #0f172a; color: white; font-size: 0.75rem; text-transform: uppercase; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  .signatures {{ margin-top: 40px; padding-top: 20px; border-top: 1px dashed #cbd5e1; display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center; }}
  .sig-block {{ border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px 10px; background: #fafafa; font-size: 0.85rem; }}
  .sig-line {{ height: 45px; }}
  @media print {{
    body {{ background: transparent; padding: 0; }}
    .toolbar {{ display: none !important; }}
    .report-container {{ border: none; padding: 0; box-shadow: none; max-width: 100%; }}
  }}
</style>
</head>
<body>

<div class="toolbar">
  <span style="font-weight: 700; font-size: 0.95rem;">📊 CX & NPS Müşteri Memnuniyeti Yönetici Raporu</span>
  <div style="display: flex; gap: 8px;">
    <a href="/api/export-csv" style="background: #10b981; color: white; text-decoration: none; padding: 8px 14px; border-radius: 6px; font-weight: bold; font-size: 0.85rem;">📥 Excel CSV İndir</a>
    <button onclick="window.print()" style="background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 0.85rem;">🖨️ Yazdır / PDF Kaydet</button>
  </div>
</div>

<div class="report-container">
  <div class="report-header">
    <div class="header-left">
      <h1>MÜŞTERİ DENEYİMİ (CX) & NPS PERFORMANS YÖNETİCİ RAPORU</h1>
      <p>Şirket: <b>{escape(company)}</b> | Rapor Tarihi: {report_date}</p>
    </div>
    <div class="header-right">
      <b>Toplam Yanıt:</b> {metrics['total_count']} Müşteri<br>
      <b>Geri Arama Talebi:</b> {metrics['callback_requests_count']} Kişi<br>
      <b>Metodoloji:</b> Net Promoter Score (NPS 0-10)
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card" style="border-left-color: {nps_color};">
      <div class="kpi-title">Net Promoter Score (NPS)</div>
      <div class="kpi-value" style="color: {nps_color};">{nps:+d}</div>
      <small style="color: #64748b;">Hedef: > +50</small>
    </div>
    <div class="kpi-card" style="border-left-color: #10b981;">
      <div class="kpi-title">Genel Memnuniyet (CSAT)</div>
      <div class="kpi-value" style="color: #10b981;">%{csat['overall_csat']:.1f}</div>
      <small style="color: #64748b;">4-5 Yıldız Oranı</small>
    </div>
    <div class="kpi-card" style="border-left-color: #16a34a;">
      <div class="kpi-title">Tavsiye Edenler (Promoters)</div>
      <div class="kpi-value" style="color: #16a34a;">%{metrics['promoters_pct']:.1f}</div>
      <small style="color: #64748b;">{metrics['promoter_count']} Müşteri (9-10 Puan)</small>
    </div>
    <div class="kpi-card" style="border-left-color: #dc2626;">
      <div class="kpi-title">Kötüleyenler (Detractors)</div>
      <div class="kpi-value" style="color: #dc2626;">%{metrics['detractors_pct']:.1f}</div>
      <small style="color: #64748b;">{metrics['detractor_count']} Churn Riski (0-6 Puan)</small>
    </div>
  </div>

  <div class="breakdown-grid">
    <div class="box">
      <div class="box-title">📊 NPS Segment Dağılımı (Müşteri Sadakati)</div>
      <div class="segment-bar">
        <div class="seg-p" style="width: {max(5.0, metrics['promoters_pct'])}%;">%{metrics['promoters_pct']}</div>
        <div class="seg-pass" style="width: {max(5.0, metrics['passives_pct'])}%;">%{metrics['passives_pct']}</div>
        <div class="seg-d" style="width: {max(5.0, metrics['detractors_pct'])}%;">%{metrics['detractors_pct']}</div>
      </div>
      <div style="font-size: 0.82rem; line-height: 1.8;">
        🟩 <b>Tavsiye Edenler (9-10):</b> {metrics['promoter_count']} Kişi (%{metrics['promoters_pct']})<br>
        🟨 <b>Pasifler (7-8):</b> {metrics['passive_count']} Kişi (%{metrics['passives_pct']})<br>
        🟥 <b>Kötüleyenler (0-6):</b> {metrics['detractor_count']} Kişi (%{metrics['detractors_pct']})
      </div>
    </div>
    <div class="box">
      <div class="box-title">⭐ Kategori Bazlı Memnuniyet (5 Üzerinden)</div>
      <div style="font-size: 0.83rem; line-height: 2;">
        📦 <b>Ürün / Hizmet Kalitesi:</b> {metrics['avg_product']} / 5.0 (CSAT: %{csat['product_csat']})<br>
        🎧 <b>Müşteri Desteği & İletişim:</b> {metrics['avg_support']} / 5.0 (CSAT: %{csat['support_csat']})<br>
        ⚡ <b>Teslimat / Süreç Hızı:</b> {metrics['avg_speed']} / 5.0 (CSAT: %{csat['speed_csat']})<br>
        💎 <b>Fiyat / Performans Değeri:</b> {metrics['avg_value']} / 5.0 (CSAT: %{csat['value_csat']})
      </div>
    </div>
  </div>

  <div style="margin-bottom: 20px;">
    <div style="font-size: 0.95rem; font-weight: 700; color: #dc2626; margin-bottom: 8px;">
      🚨 Acil Müdahale & Churn Riski Taşıyan Müşteriler (0-6 Kötüleyenler)
    </div>
    <table>
      <thead>
        <tr>
          <th style="width: 100px;">Takip Kodu</th>
          <th style="width: 150px;">Müşteri</th>
          <th style="width: 70px; text-align: center;">Skor</th>
          <th>Şikayet / Geri Bildirim Detayı</th>
          <th style="width: 90px;">Sipariş</th>
          <th style="width: 90px;">Durum</th>
        </tr>
      </thead>
      <tbody>
        {detractor_tbody}
      </tbody>
    </table>
  </div>

  <div class="signatures">
    <div class="sig-block">
      <b>Müşteri Deneyimi (CX) Uzmanı</b><br>
      Analiz & Raporlama<br>
      <div class="sig-line"></div>
      İmza / Tarih
    </div>
    <div class="sig-block">
      <b>Müşteri İlişkileri Direktörü</b><br>
      Kurtarma Aksiyonları Onayı<br>
      <div class="sig-line"></div>
      İmza / Tarih
    </div>
    <div class="sig-block">
      <b>Genel Müdür / Yönetim</b><br>
      Genel Şirket Onayı<br>
      <div class="sig-line"></div>
      İmza / Tarih
    </div>
  </div>
</div>

</body>
</html>"""

def generate_nps_csv_export(feedbacks):
    """
    Excel uyumlu UTF-8 with BOM formatında Türkçe karakter korumalı CSV dökümü üretir.
    """
    lines = [
        "Takip Kodu;Tarih;Musteri Adi;Iletisim;NPS Skoru;Segment;Urun Kalitesi;Destek Hizi;Surec Hizi;Fiyat Deger;Siparis Ref;Geri Arama;Durum;Cozum Notu;Geri Bildirim Metni"
    ]

    for f in feedbacks:
        code = str(f.get("tracking_code", "")).replace(";", " ")
        date_str = str(f.get("created_at", "")).replace(";", " ")
        name = str(f.get("customer_name", "Anonim")).replace(";", " ")
        contact = str(f.get("customer_contact", "")).replace(";", " ")
        score = int(f.get("nps_score", 0))

        if score >= 9:
            tier = "Promoter (Tavsiye Eden)"
        elif score <= 6:
            tier = "Detractor (Kotuleyen)"
        else:
            tier = "Passive (Pasif)"

        rp = f.get("rate_product", 5)
        rs = f.get("rate_support", 5)
        rsp = f.get("rate_speed", 5)
        rv = f.get("rate_value", 5)
        order = str(f.get("order_ref", "")).replace(";", " ")
        callback = str(f.get("callback_requested", "")).replace(";", " ")
        status = str(f.get("status", "")).replace(";", " ")
        note = str(f.get("resolution_note", "")).replace(";", " ").replace("\n", " ")
        text = str(f.get("feedback_text", "")).replace(";", " ").replace("\n", " ")

        row = f'"{code}";"{date_str}";"{name}";"{contact}";{score};"{tier}";{rp};{rs};{rsp};{rv};"{order}";"{callback}";"{status}";"{note}";"{text}"'
        lines.append(row)

    return "\ufeff" + "\n".join(lines)
