import pickle
import pandas as pd
import os
import sys
from datetime import datetime

# Yolları ayarla
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.weather_service import get_weather_data
from utils.tesisler import TESISLER

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

def predict_occupancy(tesis_id, rezervasyon=10, sinav_vakti=0):
    if not os.path.exists(MODEL_PATH):
        return "HATA: model.pkl yok!"

    # 1. Modeli ve Özellik Listesini Yükle
    with open(MODEL_PATH, "rb") as f:
        data = pickle.load(f)
    
    model, scaler, features = data["model"], data["scaler"], data["features"]

    # 2. Canlı Verileri Topla
    weather = get_weather_data()
    simdi = datetime.now()
    
    # 3. Veriyi Model Formatına Getir (Hata almamak için kolon isimleri train ile aynı olmalı)
    input_df = pd.DataFrame([{
        "tesis_id": tesis_id,
        "saat": simdi.hour,
        "hafta_sonu": 1 if simdi.weekday() >= 5 else 0,
        "resmi_tatil": 0,
        "etkinlik_var": 0,
        "sinav_haftasi": sinav_vakti,
        "rezervasyon_sayisi": rezervasyon,
        "sicaklik": weather["hava_sicakligi"], # Servisten gelen veriyi modelin beklediği isme atadık
        "yagis_var": weather["yagis_var"]
    }])

    # 4. Sadece modelin beklediği FEATURES listesini, doğru sırayla seç ve ölçeklendir
    X_scaled = scaler.transform(input_df[features])
    
    # 5. Tahmin
    tahmin = model.predict(X_scaled)[0]
    tahmin = max(0, min(100, tahmin)) # %0-100 arası sınırla

    tesis_adi = next((t["isim"] for t in TESISLER if t["tesis_id"] == tesis_id), "Bilinmeyen Tesis")
    
    return {
        "tesis": tesis_adi,
        "doluluk": f"%{tahmin:.0f}",
        "sicaklik": f"{weather['hava_sicakligi']}°C"
    }

if __name__ == "__main__":
    print("\n--- Nilüfer Sosyal Tesis Canlı Tahmin ---")
    try:
        res = predict_occupancy(tesis_id=1)
        print(f"Sonuç: {res}")
    except Exception as e:
        print(f"HATA: {e}")

    # Tüm tesisler için örnek tahmin
    print("\n--- Tüm Tesisler İçin Örnek Tahminler ---")
    for tesis in TESISLER[:5]:  # İlk 5 tanesi
        try:
            res = predict_occupancy(tesis_id=tesis["tesis_id"])
            print(f"{tesis['isim']}: {res['doluluk']}")
        except Exception as e:
            print(f"{tesis['isim']}: HATA - {e}")
