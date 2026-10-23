# KOBİ Müşteri Memnuniyeti ve NPS Değerlendirme Portalı

[![CI Test Suite](https://github.com/eimza-kep/kobi-musteri-memnuniyet-nps-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-musteri-memnuniyet-nps-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kobi-musteri-memnuniyet-nps-scripti/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](Dockerfile)

KOBİ'ler, e-ticaret siteleri, B2B hizmet firmaları ve danışmanlık şirketleri için harici bağımlılık gerektirmeyen (zero-dependency), **Net Promoter Score (NPS 0-10)** ve çok kriterli memnuniyet anketi toplayan, **otomatik NPS formülü hesaplayan**, **memnun müşterileri doğrudan Google & Yandex Haritalar yorumuna yönlendiren** ve **kötüleyen müşteriler (0-6 Detractors) için anında WhatsApp/E-Posta/Webhook acil kurtarma alarmı üreten** açık kaynaklı müşteri deneyimi (CX) yazılımı.

---

## 🎯 Temel Yetenekler ve Yenilikler

### 1. 🌟 Google Haritalar & Yandex Yorum Yönlendirme Kancası (Review Hook)
- **Tavsiye Edenler (9-10 Promoters):** Marka elçisi olan mutlu müşteriler, anket tamamlandığında doğrudan işletmenin **Google Haritalar 5 Yıldızlı Yorum Yazma Ekranına** (`https://search.google.com/local/writereview?placeid=...`) veya **Yandex Haritalar** profiline yönlendirilir.
- KOBİ'nin yerel SEO ve Google Haritalar itibarını organik biçimde katlar.
- Yönetim panelinden tek tıkla işletme profili URL'leri güncellenebilir.

### 2. 🚨 Negatif NPS (0-6 Kötüleyenler) İçin Acil Müdahale & WhatsApp Telafi Paketi
- **Kötüleyenler (0-6 Detractors):** Puan verildiği anda sistem tarafından otomatik olarak **"Acil İnceleme Bekliyor / Churn Riski"** bayrağı konur.
- **WhatsApp Telafi Mesajı:** Müşteriye özelleştirilmiş, nazik bir özür ve telafi mesajı şablonu üretilir (`wa.me` doğrudan bağlantısı).
- **Hızlı Arama Butonu:** Yönetim panelinde tek tıkla müşteriyi arama (`tel:...`).
- **Acil Webhook & Dahili Bildirim:** Şikayet verisi (Müşteri, İletişim, Puan, Şikayet Metni, Sipariş No) şirket içi Slack, Microsoft Teams, CRM veya e-posta kanalına 15 dakika içinde aksiyon alınması için JSON webhook olarak iletilir.
- **Çözüm Notu Kaydı:** Alınan aksiyonlar ve telafi notları sistemde kalıcı olarak saklanır.

### 3. 📊 NPS Analitik ve Metrik Motoru
- **Canlı NPS Formülü Hesabı:**
  $$\text{NPS} = \left(\frac{\text{Tavsiye Edenler (9-10)} - \text{Kötüleyenler (0-6)}}{\text{Toplam Yanıt}}\right) \times 100$$
- **Segment Dağılımı:** Promoters (% ve sayı), Passives (% ve sayı), Detractors (% ve sayı).
- **Kategori Ortalamaları:** Ürün kalitesi, destek hızı, iletişim ve fiyat/değer dengesi için 5 üzerinden puan ortalamaları.
- **Excel Uyumlu Dışa Aktarım:** UTF-8 BOM destekli Türkçe karakter korumalı tek tıkla CSV çıktısı.

---

## 🚀 Hızlı Başlangıç

### Windows (Tek Tıkla Çalıştır)
1. Repoyu klonlayın veya zip olarak indirin.
2. `Baslat.bat` dosyasına çift tıklayın.
3. Otomatik olarak açılır:
   - **NPS Anket Formu:** `http://localhost:8091`
   - **Yönetim & Analitik Paneli:** `http://localhost:8091/admin`

### Linux & macOS
```bash
git clone https://github.com/eimza-kep/kobi-musteri-memnuniyet-nps-scripti.git
cd kobi-musteri-memnuniyet-nps-scripti
chmod +x baslat.sh
./baslat.sh
```

### Docker ile Çalıştırma
```bash
docker build -t kobi-nps-scripti .
docker run -d -p 8091:8091 --name nps-app kobi-nps-scripti
```

### PHP / Paylaşımlı Hosting (cPanel / Plesk)
Dosyaları sunucunuzdaki `/nps/` veya `/anket/` dizinine yükleyin. `api.php` otomatik olarak JSON veritabanını oluşturup yönetecektir.

---

## ⚙️ Yapılandırma ve Harita Ayarları

Yönetim Panelinde (`/admin`) yer alan **"⚙️ NPS & Harita Ayarları"** menüsünden aşağıdaki ayarları yapabilirsiniz:

| Parametre | Açıklama | Örnek Değer |
| :--- | :--- | :--- |
| `company_name` | Şirket veya Marka Adı | ABC Lojistik A.Ş. |
| `google_maps_url` | Google Haritalar Yorum Bağlantısı | `https://search.google.com/local/writereview?placeid=ChIJ...` |
| `yandex_maps_url` | Yandex Haritalar Profil Bağlantısı | `https://yandex.com.tr/haritalar/org/...` |
| `detractor_threshold` | Negatif NPS Eşik Değeri (Risk) | `6` (0-6 arası) |
| `promoter_threshold` | Pozitif NPS Eşik Değeri | `9` (9-10) |
| `webhook_url` | Acil Şikayet Webhook Endpoint | `https://hooks.slack.com/services/...` |
| `alert_email` | Acil Bildirim E-Posta Adresi | `destek@sirketiniz.com` |

---

## 📡 REST API Referansı

| Metot | Uç Nokta | Açıklama |
| :--- | :--- | :--- |
| `POST` | `/api/nps-gonder` | Müşteri NPS anketini kaydeder, Harita yönlendirme ve acil durum kancasını döner. |
| `GET` | `/api/nps-listesi` | Tüm anket yanıtlarını listeler. |
| `GET` | `/api/nps-metrikler` | Toplam yanıt, NPS puanı ve kategori ortalamalarını hesaplar. |
| `GET` | `/api/detractor-alert?tracking_code=...` | Kötüleyen müşteri için WhatsApp, tel linki ve dahili uyarı paketini döner. |
| `POST` | `/api/durum-guncelle` | İnceleme durumunu ve çözüm notunu günceller. |
| `GET` | `/api/ayarlar` | Sistem ayarlarını ve harita bağlantılarını getirir. |
| `POST` | `/api/ayarlar` | Sistem ayarlarını kalıcı olarak kaydeder. |

---

## 📊 Dosya Mimarisi

```
kobi-musteri-memnuniyet-nps-scripti/
├── index.html              # Müşteri NPS anket formu ve teşekkür/harita ekranı
├── admin.html              # Müşteri deneyimi, NPS analitik ve şikayet yönetim paneli
├── server.py               # SQLite veritabanlı standalone Python HTTP sunucusu
├── api.php                 # PHP tabanlı REST backend
├── Dockerfile              # Container dağıtım dosyası
├── Baslat.bat              # Windows tek tıkla başlatıcı
├── baslat.sh               # Linux / macOS başlatıcı
├── scripts/
│   ├── nps_analytics_engine.py  # NPS hesaplama motoru, churn uyarısı & harita kancası
│   └── test_nps.py              # Otomatik birim test paketi
├── .github/
│   └── workflows/ci.yml         # GitHub Actions CI testi
└── README.md                    # Dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

Tüm fonksiyonları ve entegrasyonları test etmek için:

```bash
python scripts/test_nps.py
```

---

## 🌐 KOBİ & E-Dönüşüm Açık Kaynak Ekosistemi

Bu müşteri deneyim aracı, [@eimza-kep](https://github.com/eimza-kep) açık kaynak ekosisteminin KOBİ geri bildirim ve itibar modülüdür. İlgili diğer araçlar:

* 🏢 [kobi-hizli-teklif-scripti](https://github.com/eimza-kep/kobi-hizli-teklif-scripti) - Satış teklifi ve sipariş sonrası müşteri memnuniyet ölçümü.
* 📦 [kobi-tedarikci-teklif-toplama-scripti](https://github.com/eimza-kep/kobi-tedarikci-teklif-toplama-scripti) - Tedarikçi RFQ karşılaştırma ve satınalma sözleşmesi oluşturma.
* 🔧 [kobi-servis-ariza-takip-scripti](https://github.com/eimza-kep/kobi-servis-ariza-takip-scripti) - Teknik servis ve onarım tamamlandıktan sonra anlık NPS anketi tetikleyici.
* 🔒 [kurumsal-kvkk-basvuru-scripti](https://github.com/eimza-kep/kurumsal-kvkk-basvuru-scripti) - Müşteri anket verileri ve iletişim izinleri için KVKK uyum portali.
* 🌟 [awesome-turkiye-e-donusum](https://github.com/eimza-kep/awesome-turkiye-e-donusum) - Türkiye e-Dönüşüm açık kaynak araçları ve kütüphaneleri kürasyonu.

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
