# Nilüfer Sosyal Tesis AI Sistemi

AI destekli sosyal tesis doluluk tahmin sistemi. Nilüfer Belediyesi'nin 12 farklı sosyal tesisinin doluluk oranlarını gerçek zamanlı olarak tahmin eder.

## 🚀 Özellikler

- **12 Tesis**: Kütüphaneler, müzeler, gençlik merkezleri, kafeler ve lokanta
- **AI Tahmin**: Multi-Linear Regression ile %70+ doğruluk
- **Hava Durumu**: OpenWeatherMap entegrasyonu
- **Web Arayüzü**: Modern, responsive frontend
- **REST API**: FastAPI ile backend servisleri
- **3 Kişilik Takım**: Backend, AI, Frontend ayrımı

## 📁 Proje Yapısı

```
nilufer-sosyal-tesis-ai/
│
├── backend/                    # Backend Geliştirici
│   ├── app.py                 # FastAPI ana uygulama
│   └── requirements.txt       # Backend bağımlılıkları
│
├── ai/                        # AI Geliştirici
│   ├── train_model.py         # Model eğitimi
│   ├── predict.py             # Tahmin fonksiyonları
│   ├── model.pkl              # Eğitilmiş model
│   └── features.py            # Özellik tanımları
│
├── data/                      # Veri
│   └── sentetik_ziyaretci.csv # Sentetik eğitim verisi
│
├── utils/                     # Ortak Araçlar
│   ├── data_generator.py      # Veri üretimi
│   ├── weather_service.py     # Hava durumu servisi
│   └── tesisler.py           # Tesis bilgileri
│
├── frontend/                  # Frontend Geliştirici
│   ├── index.html            # Ana sayfa
│   ├── style.css             # Stil dosyası
│   └── script.js             # JavaScript
│
└── README.md                  # Bu dosya
```

## 🛠️ Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.8+
- pip

### 1. Bağımlılıkları Yükleme

```bash
# Ana bağımlılıkları yükle (pandas, numpy, scikit-learn, vb.)
pip install -r requirements.txt

# Backend için ek bağımlılıkları yükle
cd backend
pip install -r requirements.txt
cd ..
```

### 2. Backend Çalıştırma

```bash
cd backend
python app.py
```

Backend `http://localhost:8000` adresinde çalışacak.

### 2. AI Model Eğitimi

```bash
cd ai
python train_model.py
```

### 3. Frontend Çalıştırma

```bash
cd frontend
# Yerel sunucu ile açın (örnek: python -m http.server 3000)
# Veya doğrudan index.html'i tarayıcıda açın
```

### 4. API Test

```bash
# Sağlık kontrolü
curl http://localhost:8000/health

# Tesis listesi
curl http://localhost:8000/tesisler

# Tek tesis tahmini
curl "http://localhost:8000/tahmin/1"

# Tüm tesisler tahmini
curl "http://localhost:8000/tum-tesisler-tahmin"
```

## 🎯 Tesisler

| ID | Tesis Adı | Tip | Kapasite |
|----|-----------|-----|----------|
| 1 | Nilbel Koza Kütüphanesi | Kütüphane | 180 |
| 2 | Şiir Kütüphanesi | Kütüphane | 60 |
| 3 | Akkılıç Kütüphanesi | Kütüphane | 120 |
| 4 | Nilüfer Fotoğraf Müzesi | Müze | 100 |
| 5 | Sağlık Müzesi | Müze | 70 |
| 6 | Edebiyat Müzesi | Müze | 90 |
| 7 | 29 Ekim Kafe | Kafe | 120 |
| 8 | Kafe Pancar | Kafe | 90 |
| 9 | Nilüfer Kent Lokantası | Lokanta | 150 |
| 10 | Beşevler Gençlik Merkezi | Gençlik Merkezi | 200 |
| 11 | Altınşehir Gençlik Merkezi | Gençlik Merkezi | 150 |
| 12 | Cumhuriyet Gençlik Merkezi | Gençlik Merkezi | 130 |

## 🔧 Geliştirme Rehberi

### Backend Geliştirici
- `backend/app.py`: API endpoint'lerini geliştirin
- CORS ayarları, authentication ekleyin
- Veritabanı entegrasyonu yapın

### AI Geliştirici
- `ai/train_model.py`: Daha iyi modeller deneyin
- `ai/features.py`: Yeni özellikler ekleyin
- Model performansını iyileştirin

### Frontend Geliştirici
- `frontend/`: UI/UX iyileştirmeleri
- Responsive tasarım
- Gerçek zamanlı güncellemeler

## 📊 API Endpoints

### Temel Endpoints
- `GET /` - API ana sayfası ve bilgi
- `GET /health` - Sistem sağlık kontrolü
- `GET /docs` - FastAPI otomatik dokümantasyon

### Tesis Endpoints
- `GET /tesisler` - Tüm tesislerin listesi
- `GET /tesis/{tesis_id}` - Belirli tesis bilgileri

### Tahmin Endpoints
- `GET /tahmin/{tesis_id}?rezervasyon=10&sinav_vakti=0` - Tek tesis doluluk tahmini
- `GET /tum-tesisler-tahmin?rezervasyon=10&sinav_vakti=0` - Tüm tesisler doluluk tahminleri

### Sistem Endpoints
- `GET /istatistikler` - Sistem istatistikleri

### Query Parameters
- `rezervasyon` (int): Rezervasyon sayısı (varsayılan: 10)
- `sinav_vakti` (int): Sınav haftası (0/1, varsayılan: 0)

## 🔐 Environment Variables

```bash
# .env dosyası oluşturun
OPENWEATHER_API_KEY=your_api_key_here
```

## 🚀 Production Deployment

1. Backend'i production sunucusuna deploy edin
2. Frontend'i CDN'e yükleyin
3. API key'ini güvenli şekilde saklayın
4. HTTPS sertifikası ekleyin

## 📈 Performans Metrikleri

- Model Doğruluğu: %71.86 R²
- API Response Time: <100ms
- Frontend Load Time: <2s

## 🤝 Katkıda Bulunma

1. Branch oluşturun
2. Değişikliklerinizi commit edin
3. Pull request açın
4. Code review'dan geçirin

## 📄 Lisans

Bu proje Nilüfer Belediyesi adına geliştirilmiştir.
