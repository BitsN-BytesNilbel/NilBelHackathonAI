import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import os

# Dosya yolları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "sentetik_ziyaretci.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

def train_model():
    """Nilüfer Sosyal Tesis projesi için Multi Linear Regression eğitir."""
    if not os.path.exists(DATA_PATH):
        print(f"HATA: {DATA_PATH} bulunamadı!")
        return

    # 1. Veri Yükle
    df = pd.read_csv(DATA_PATH)
    
    # 2. Özellikler (Features) - Predict dosyasıyla tam uyumlu olmalı
    FEATURES = [
        "tesis_id", "saat", "hafta_sonu", "resmi_tatil", 
        "etkinlik_var", "sinav_haftasi", "rezervasyon_sayisi", 
        "sicaklik", "yagis_var"
    ]
    TARGET = "doluluk_orani"

    X = df[FEATURES]
    y = df[TARGET]

    # 3. Ölçeklendirme (Scaling)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Model Eğitimi
    model = LinearRegression()
    model.fit(X_scaled, y)

    # 5. Kayıt (Her şeyi tek pakette topluyoruz)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({
            "model": model, 
            "scaler": scaler, 
            "features": FEATURES
        }, f)

    # 6. Performans Çıktısı
    r2 = r2_score(y, model.predict(X_scaled))
    mae = mean_absolute_error(y, model.predict(X_scaled))
    print(f"--- Model Başarıyla Eğitildi ---")
    print(f"R2 Skoru: {r2:.4f} | Ortalama Hata: %{mae:.2f}")

if __name__ == "__main__":
    train_model()