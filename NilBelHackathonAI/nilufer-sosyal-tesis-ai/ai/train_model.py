import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.utils.class_weight import compute_sample_weight
import pickle
import os

# Dosya yolları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
SENTETIC_DATA_PATH = os.path.join(DATA_DIR, "sentetik_ziyaretci.csv")
REAL_DATA_PATH = os.path.join(DATA_DIR, "gercek_ziyaretci.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

def train_hybrid_model():
    """
    Hibrit Eğitim: Sentetik + Gerçek veriyi birleştirerek model eğitir.
    Gerçek veriye daha yüksek ağırlık verir (Sample Weighting).
    """
    print("--- Hibrit Model Eğitimi Başlatıldı ---")

    # 1. Sentetik veriyi yükle (baseline)
    synthetic_df = None
    if os.path.exists(SENTETIC_DATA_PATH):
        synthetic_df = pd.read_csv(SENTETIC_DATA_PATH)
        print(f"Sentetik veri yüklendi: {len(synthetic_df)} kayıt")
    else:
        print(f"UYARI: Sentetik veri bulunamadı: {SENTETIC_DATA_PATH}")

    # 2. Gerçek veriyi yükle
    real_df = None
    if os.path.exists(REAL_DATA_PATH):
        real_df = pd.read_csv(REAL_DATA_PATH)
        print(f"Gerçek veri yüklendi: {len(real_df)} kayıt")
    else:
        print(f"BİLGİ: Gerçek veri henüz yok, sadece sentetik veri ile eğitim yapılacak")

    # 3. Veri birleştirme
    if synthetic_df is not None and real_df is not None:
        # Ortak kolonları kontrol et
        common_cols = set(synthetic_df.columns) & set(real_df.columns)
        if not common_cols:
            print("HATA: Sentetik ve gerçek veri kolonları uyumsuz!")
            return

        # Sadece ortak kolonları kullan
        synthetic_df = synthetic_df[list(common_cols)]
        real_df = real_df[list(common_cols)]

        # Birleştir
        combined_df = pd.concat([synthetic_df, real_df], ignore_index=True)

        # Sample weights: Gerçek veriye 3x daha yüksek ağırlık
        sample_weights = np.ones(len(combined_df))
        sample_weights[len(synthetic_df):] = 3.0  # Son kısım gerçek veri

        print(f"Birleştirilmiş veri: {len(combined_df)} kayıt (Sentetik: {len(synthetic_df)}, Gerçek: {len(real_df)})")

    elif synthetic_df is not None:
        combined_df = synthetic_df
        sample_weights = np.ones(len(combined_df))
        print("Sadece sentetik veri ile eğitim yapılacak")

    elif real_df is not None:
        combined_df = real_df
        sample_weights = np.ones(len(combined_df)) * 2.0  # Gerçek veri mevcut, yüksek ağırlık
        print("Sadece gerçek veri ile eğitim yapılacak")

    else:
        print("HATA: Eğitim için hiç veri bulunamadı!")
        return

    # 4. Özellikler ve hedef
    FEATURES = [
        "tesis_id", "saat", "hafta_sonu", "resmi_tatil",
        "etkinlik_var", "sinav_haftasi", "rezervasyon_sayisi",
        "sicaklik", "yagis_var"
    ]
    TARGET = "doluluk_orani"

    # Eksik kolonları kontrol et
    missing_features = [f for f in FEATURES if f not in combined_df.columns]
    if missing_features:
        print(f"HATA: Eksik özellikler: {missing_features}")
        return

    X = combined_df[FEATURES]
    y = combined_df[TARGET]

    # 5. Veri temizliği
    # NaN değerleri doldur
    X = X.fillna(X.mean())
    y = y.fillna(y.mean())

    print(f"Eğitim verisi: {len(X)} örnek, {len(FEATURES)} özellik")

    # 6. Ölçeklendirme
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 7. Sample weight normalization
    sample_weights = sample_weights / np.sum(sample_weights) * len(sample_weights)

    # 8. Model eğitimi (Sample Weight ile)
    model = LinearRegression()
    model.fit(X_scaled, y, sample_weight=sample_weights)

    # 9. Model kaydetme
    model_data = {
        "model": model,
        "scaler": scaler,
        "features": FEATURES,
        "training_info": {
            "total_samples": len(combined_df),
            "synthetic_samples": len(synthetic_df) if synthetic_df is not None else 0,
            "real_samples": len(real_df) if real_df is not None else 0,
            "sample_weighting": "enabled",
            "trained_at": pd.Timestamp.now().isoformat()
        }
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_data, f)

    # 10. Performans değerlendirmesi
    y_pred = model.predict(X_scaled)
    r2 = r2_score(y, y_pred, sample_weight=sample_weights)
    mae = mean_absolute_error(y, y_pred, sample_weight=sample_weights)

    print("\n--- Hibrit Model Başarıyla Eğitildi ---")
    print(f"R² Skoru: {r2:.4f}")
    print(f"Ağırlıklı MAE: %{mae:.2f}")
    print(f"Sample Weight Etkisi: {'Aktif' if len(sample_weights) > 1 else 'Pasif'}")

    # Özellik önemleri
    feature_importance = dict(zip(FEATURES, np.abs(model.coef_)))
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

    print("\n--- Özellik Önem Sıralaması ---")
    for feature, importance in sorted_features[:5]:
        print(f"{feature}: {importance:.4f}")

    return model_data

def retrain_if_needed():
    """
    Gerektiğinde modeli yeniden eğitir (örneğin yeni gerçek veri eklendiğinde)
    """
    real_data_path = os.path.join(DATA_DIR, "gercek_ziyaretci.csv")

    if os.path.exists(real_data_path):
        try:
            real_df = pd.read_csv(real_data_path)
            record_count = len(real_df)

            # Her 50 yeni gerçek veri için yeniden eğit
            if record_count > 0 and record_count % 50 == 0:
                print(f"[RETRAIN] {record_count} gerçek veri kaydı - Otomatik yeniden eğitim başlatılıyor...")
                train_hybrid_model()
                print("[RETRAIN] Model başarıyla güncellendi!")

        except Exception as e:
            print(f"[RETRAIN] Hata: {e}")

if __name__ == "__main__":
    # Ana eğitim
    train_hybrid_model()

    # Retrain kontrolü
    retrain_if_needed()
