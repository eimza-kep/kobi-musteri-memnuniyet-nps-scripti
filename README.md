# KOBİ Müşteri Memnuniyeti ve NPS Değerlendirme Portalı

[![CI Test Suite](https://github.com/eimza-kep/kobi-musteri-memnuniyet-nps-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kobi-musteri-memnuniyet-nps-scripti/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)

KOBİ'ler, e-ticaret siteleri, B2B hizmet firmaları ve danışmanlık şirketleri için harici bağımlılık gerektirmeyen (zero-dependency), **Net Promoter Score (NPS 0-10)** ve çok kriterli memnuniyet anketi toplayan, **otomatik NPS formülü hesaplayan** ve **kötüleyen müşteriler (detractors) için acil risk alarmı veren** açık kaynaklı müşteri deneyimi (CX) yazılımı.

---

## 🎯 Temel Yetenekler

- **İnteraktif 0-10 NPS Seçici:** Tavsiye skoruna göre anlık segmentasyon:
  - **9 - 10 (Promoters / Tavsiye Edenler):** Marka elçileri.
  - **7 - 8 (Passives / Pasifler):** Memnun ancak sadakati zayıf kitle.
  - **0 - 6 (Detractors / Kötüleyenler):** Otomatik **"Acil İnceleme / Churn Riski"** statüsü tetikler.
- **Çok Kriterli 5 Yıldız Değerlendirmesi:** Ürün/hizmet kalitesi, destek & iletişim, teslimat hızı ve fiyat/değer dengesi.
- **Açık Uçlu Görüş & Geri Arama Talebi:** Müşterinin talebi doğrultusunda doğrudan aranma opsiyonu.
- **Müşteri Deneyimi & Yönetim Paneli (`/admin`):**
  - Canlı **NPS Formülü Hesabı**: `% Promoters - % Detractors = NPS (-100 ile +100 arası)`.
  - Müşteri segment dağılımları ve memnuniyet ortalamaları.
  - Durum takibi: "Kayıt Alındı", "Acil İnceleme Bekliyor", "Müşteri ile Görüşüldü", "Memnuniyet Sağlandı".
  - Excel uyumlu UTF-8 BOM destekli tek tıkla **CSV Dışa Aktarımı**.
- **Sıfır Bağımlılık (Zero-Dependency):**
  - **Python Motoru:** Dahili SQLite veritabanı ile tek tıkla lokalde veya sunucuda çalışır (`server.py`).
  - **PHP Motoru:** Paylaşımlı hosting ve cPanel için hazır JSON REST backend (`api.php`).
  - **Offline Mod:** İnternetsiz çalışma ve tarayıcı yerel hafızası (`localStorage`) desteği.

---

## 🚀 Hızlı Başlangıç

### Windows (Tek Tıkla Çalıştır)
1. Repoyu klonlayın veya indirin.
2. `Baslat.bat` dosyasına çift tıklayın.
3. Otomatik olarak açılır:
   - NPS Anket Formu: `http://localhost:8091`
   - Yönetim Paneli: `http://localhost:8091/admin`

### Linux & macOS
```bash
git clone https://github.com/eimza-kep/kobi-musteri-memnuniyet-nps-scripti.git
cd kobi-musteri-memnuniyet-nps-scripti
chmod +x baslat.sh
./baslat.sh
```

### PHP / Paylaşımlı Hosting
Dosyaları sunucunuzdaki `/nps/` veya `/anket/` dizinine yükleyin. `api.php` otomatik olarak JSON veritabanını oluşturup yönetecektir.

---

## 📊 Mimari ve Dosya Yapısı

```
kobi-musteri-memnuniyet-nps-scripti/
├── index.html              # Müşteri NPS anket formu ve teşekkür ekranı
├── admin.html              # Müşteri deneyimi, NPS formül hesabı ve takip paneli
├── server.py               # Standalone Python SQLite HTTP sunucusu (Port 8091)
├── api.php                 # PHP tabanlı REST backend
├── Baslat.bat              # Windows tek tıkla başlatıcı
├── baslat.sh               # Linux / macOS başlatıcı
├── scripts/
│   └── test_nps.py         # Otomatik test paketi
├── .github/
│   └── workflows/ci.yml    # GitHub Actions CI testi
└── README.md               # Dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

```bash
python scripts/test_nps.py
```

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
