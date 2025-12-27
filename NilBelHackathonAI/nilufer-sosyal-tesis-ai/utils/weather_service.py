import os
import random
import pickle
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score

# --- 1. AYARLAR VE TANIMLAMALAR ---
# Bursa/Nilüfer koordinatları
LAT = 40.1885
LON = 29.0610
API_KEY = "30f76dc3e1ef1ae6ae0e1ea0010927b4"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Nilüfer Belediyesi sosyal tesisleri
TESISLER = [
    {"tesis_id": 1, "kapasite": 120, "isim": "Nilüfer Kütüphanesi"},
    {"tesis_id": 2, "kapasite": 80, "isim": "Görükle Kütüphanesi"},
    {"tesis_id": 3, "kapasite": 200, "isim": "Nilüfer Kent Müzesi"},
    {"tesis_id": 4, "kapasite": 300, "isim": "Gençlik ve İnovasyon Merkezi"},
]

# --- 2. HAVA DURUMU SERVİSİ ---
def get_weather_data():
    """Canlı hava durumunu OpenWeather API'den çeker."""
    params = {"lat": LAT, "lon": LON, "appid": API_KEY, "units": "metric", "lang": "tr"}
    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {"hava_sicakligi": data["main"]["temp"], "yagis_var": 1 if "rain" in data else 0}
    except:
        pass
    # API hatası durumunda Bursa kış fallback verisi
    return {"hava_sicakligi": round(random.uniform(2, 8), 1), "yagis_var": random.choice([0, 1])}

# --- 3. SENTETİK VERİ ÜRETİCİ (MVP Yaklaşımı) ---
def generate_data(kayit_sayisi=2000):
    """Proje dökümanı Madde 6.2'ye uygun sentetik veri üretir."""
    data = []
    for _ in range(kayit_sayisi):
        tesis = random.choice(TESISLER)
        saat = random.randint(9, 22)
        gun = random.randint(1, 7)
        hafta_sonu = 1 if gun >= 6 else 0
        resmi_tatil = np.random.binomial(1, 0.05)
        sinav_haftasi = np.random.binomial(1, 0.15)
        etkinlik_var = np.random.binomial(1, 0.1)
        rezervasyon = random.randint(0, 40)
        sicaklik = random.uniform(0, 35)
        yagis = np.random.binomial(1, 0.2)
        
        # Doluluk hesaplama mantığı (Linear Logic)
        base = tesis["kapasite"] * 0.2
        etki = (saat * 2) + (hafta_sonu * 15) + (sinav_haftasi * 25) + (rezervasyon * 0.8) - (yagis * 10)
        ziyaretci = max(0, min(int(base + etki + np.random.normal(0, 5)), tesis["kapasite"]))
        
        data.append([
            tesis["tesis_id"], saat, gun, hafta_sonu, resmi_tatil,
            etkinlik_var, sinav_haftasi, rezervasyon, 50, sicaklik, yagis, (ziyaretci/tesis["kapasite"])*100
        ])
    
    cols = ["tesis_id", "saat", "gun", "hafta_sonu", "resmi_tatil", "etkinlik_var", 
            "sinav_haftasi", "rezervasyon_sayisi", "onceki_gun_ziyaretci", "hava_sicakligi", "yagis_var", "doluluk_orani"]
    return pd.DataFrame(data, columns=cols)

# --- 4. MODEL EĞİTİMİ (Multi-Linear Regression) ---
# Modelin matematiksel temeli: $Y = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \dots + \epsilon$
def train_ai_model(df):
    features = ["tesis_id", "saat", "gun", "hafta_sonu", "resmi_tatil", "etkinlik_var", 
                "sinav_haftasi", "rezervasyon_sayisi", "onceki_gun_ziyaretci", "hava_sicakligi", "yagis_var"]
    X = df[features]
    y = df["doluluk_orani"]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    # Başarı metrikleri
    r2 = r2_score(y, model.predict(X_scaled))
    print(f"Model Eğitildi. R2 Skoru: {r2:.4f}")
    
    return model, scaler, features

# --- 5. CANLI TAHMİN MEKANİZMASI ---
def predict_live(model, scaler, features, tesis_id=1):
    weather = get_weather_data()
    simdi = datetime.now()
    
    input_data = pd.DataFrame([{
        "tesis_id": tesis_id,
        "saat": simdi.hour,
        "gun": simdi.weekday() + 1,
        "hafta_sonu": 1 if simdi.weekday() >= 5 else 0,
        "resmi_tatil": 0,
        "etkinlik_var": 0,
        "sinav_haftasi": 0,
        "rezervasyon_sayisi": 10,
        "onceki_gun_ziyaretci": 50,
        "hava_sicakligi": weather["hava_sicakligi"],
        "yagis_var": weather["yagis_var"]
    }])
    
    X_scaled = scaler.transform(input_df := input_data[features])
    tahmin = model.predict(X_scaled)[0]
    
    tesis_ismi = next(t["isim"] for t in TESISLER if t["tesis_id"] == tesis_id)
    return f"{tesis_ismi} için Tahmini Doluluk: %{max(0, min(100, tahmin)):.0f} (Hava: {weather['hava_sicakligi']}°C)"

# --- 6. ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    print("--- NİLÜFER SOSYAL TESİS AI SİSTEMİ BAŞLATILIYOR ---")
    
    # 1. Veri Üret
    raw_data = generate_data()
    
    # 2. Modeli Eğit
    model, scaler, features = train_ai_model(raw_data)
    
    # 3. Canlı Tahmin Yap
    for tesis in TESISLER:
        print(predict_live(model, scaler, features, tesis["tesis_id"]))