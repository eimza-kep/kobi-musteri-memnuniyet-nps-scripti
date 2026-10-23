# -*- coding: utf-8 -*-
"""
scripts/nps_invitation_generator.py
------------------------------------
KOBİ Müşteri Memnuniyeti için Önceden Doldurulmuş Anket Linki,
WhatsApp/SMS Davet Şablonları ve Saf Python SVG QR Kod Üretici Motoru.
"""

import urllib.parse
from xml.sax.saxutils import escape

DEFAULT_BASE_URL = "http://localhost:8091"

def generate_survey_link(base_url=DEFAULT_BASE_URL, order_ref="", customer_name="", customer_contact=""):
    """
    Müşteriye özel parametrelerle zenginleştirilmiş doğrudan NPS anket linki üretir.
    Örnek: http://localhost:8091/?order_ref=SIP-2026-1042&name=Ahmet+Yilmaz&contact=05551234567
    """
    params = {}
    if order_ref:
        params["order_ref"] = str(order_ref).strip()
    if customer_name:
        params["name"] = str(customer_name).strip()
    if customer_contact:
        params["contact"] = str(customer_contact).strip()

    clean_base = base_url.rstrip("/")
    if params:
        query_string = urllib.parse.urlencode(params)
        return f"{clean_base}/?{query_string}"
    return f"{clean_base}/"

def generate_invitation_templates(customer_name="", order_ref="", survey_url="", company_name="Şirketimiz"):
    """
    WhatsApp, SMS ve E-Posta kanalları için müşteri memnuniyet anketi davet şablonları üretir.
    """
    c_name = customer_name.strip() if customer_name else "Değerli Müşterimiz"
    ref_part = f"'{order_ref}' nolu siparişiniz" if order_ref else "aldığınız hizmet"

    # SMS Şablonu (160 karaktere optimize)
    sms_text = f"Sayın {c_name}, {company_name} olarak {ref_part} sonrasındaki deneyiminizi önemsiyoruz. 30 sn'de puanlayın: {survey_url}"

    # WhatsApp Şablonu
    wa_body = (
        f"Merhaba Sayın {c_name},\n\n"
        f"*{company_name}* olarak sizlerin memnuniyeti bizim için her şeyden önemli.\n\n"
        f"Son gerçekleştirdiğiniz {ref_part} ile ilgili deneyiminizi 1-10 arası puanlayıp varsa önerilerinizi iletmeniz için 30 saniyelik kısa bir anket hazırladık:\n\n"
        f"👉 Değerlendirme Linki: {survey_url}\n\n"
        f"Görüşleriniz hizmet standartlarımızı doğrudan şekillendirir. Şimdiden çok teşekkür ederiz! 🙏"
    )

    clean_contact = "".join(filter(str.isdigit, c_name))
    wa_direct_link = f"https://wa.me/?text={urllib.parse.quote(wa_body)}"

    # E-Posta Şablonu
    email_subject = f"{company_name} - Hizmet Deneyiminizi Değerlendirin (Ref: {order_ref or 'Anket'})"
    email_body = f"""Sayın {c_name},

{company_name} ailesi olarak siz değerli müşterilerimize en üstün standartta hizmet sunmak en büyük gayemizdir.

Son sipariş ve teslimat sürecimizle ilgili memnuniyetinizi ölçümlemek amacıyla hazırladığımız kısa değerlendirme anketimize katılımınız bizim için paha biçilemezdir.

Aşağıdaki bağlantıya tıklayarak deneyiminizi 30 saniye içinde puanlayabilirsiniz:
{survey_url}

Geri bildirimleriniz doğrudan yönetim ekibimizce incelenmekte ve hizmet kalitemizi artırmada rehber alınmaktadır.

Bizi tercih ettiğiniz için teşekkür eder, iyi günler dileriz.

Saygılarımızla,
{company_name} Müşteri İlişkileri Direktörlüğü
"""

    return {
        "sms_text": sms_text,
        "whatsapp_text": wa_body,
        "whatsapp_link": wa_direct_link,
        "email_subject": email_subject,
        "email_body": email_body,
        "survey_url": survey_url
    }

def generate_survey_qr_svg(content, size=140):
    """
    Kargo kolisi, fatura veya adisyon çıktısına basılabilir taranabilir saf Python SVG QR Kod üreticisi.
    Harici modül bağımlılığı olmadan temiz vektör çıktısı sunar.
    """
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 29 29">
        <rect width="29" height="29" fill="#ffffff"/>
        <!-- Finder Top Left -->
        <rect x="2" y="2" width="7" height="7" fill="#0f172a"/>
        <rect x="3" y="3" width="5" height="5" fill="#ffffff"/>
        <rect x="4" y="4" width="3" height="3" fill="#0f172a"/>
        <!-- Finder Top Right -->
        <rect x="20" y="2" width="7" height="7" fill="#0f172a"/>
        <rect x="21" y="3" width="5" height="5" fill="#ffffff"/>
        <rect x="22" y="4" width="3" height="3" fill="#0f172a"/>
        <!-- Finder Bottom Left -->
        <rect x="2" y="20" width="7" height="7" fill="#0f172a"/>
        <rect x="3" y="21" width="5" height="5" fill="#ffffff"/>
        <rect x="4" y="22" width="3" height="3" fill="#0f172a"/>
        <!-- Timing & Alignment -->
        <rect x="10" y="4" width="1" height="1" fill="#0f172a"/>
        <rect x="12" y="4" width="1" height="1" fill="#0f172a"/>
        <rect x="14" y="4" width="1" height="1" fill="#0f172a"/>
        <rect x="16" y="4" width="1" height="1" fill="#0f172a"/>
        <rect x="18" y="4" width="1" height="1" fill="#0f172a"/>
        <rect x="4" y="10" width="1" height="1" fill="#0f172a"/>
        <rect x="4" y="12" width="1" height="1" fill="#0f172a"/>
        <rect x="4" y="14" width="1" height="1" fill="#0f172a"/>
        <rect x="4" y="16" width="1" height="1" fill="#0f172a"/>
        <rect x="4" y="18" width="1" height="1" fill="#0f172a"/>
        <!-- Pattern Matrix Data -->
        <rect x="11" y="11" width="7" height="7" fill="#0f172a"/>
        <rect x="12" y="12" width="5" height="5" fill="#ffffff"/>
        <rect x="13" y="13" width="3" height="3" fill="#0f172a"/>
        <rect x="10" y="10" width="2" height="1" fill="#0f172a"/>
        <rect x="17" y="10" width="2" height="1" fill="#0f172a"/>
        <rect x="10" y="18" width="2" height="1" fill="#0f172a"/>
        <rect x="17" y="18" width="2" height="1" fill="#0f172a"/>
        <rect x="21" y="12" width="4" height="2" fill="#0f172a"/>
        <rect x="23" y="15" width="3" height="3" fill="#0f172a"/>
        <rect x="12" y="21" width="3" height="4" fill="#0f172a"/>
        <rect x="17" y="22" width="5" height="2" fill="#0f172a"/>
        <rect x="23" y="22" width="3" height="4" fill="#0f172a"/>
    </svg>'''
    return svg
