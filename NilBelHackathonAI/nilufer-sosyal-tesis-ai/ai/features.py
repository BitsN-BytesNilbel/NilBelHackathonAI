# AI Model Özellik Listesi
# Bu dosya modelin kullandığı özellikleri tanımlar
# Değişiklik yapıldığında modeli yeniden eğitmek gerekir

FEATURES = [
    "tesis_id",
    "saat",
    "hafta_sonu",
    "resmi_tatil",
    "etkinlik_var",
    "sinav_haftasi",
    "rezervasyon_sayisi",
    "sicaklik",
    "yagis_var"
]

# Hedef değişken
TARGET = "doluluk_orani"

# Model parametreleri
MODEL_PARAMS = {
    "test_size": 0.2,
    "random_state": 42
}
