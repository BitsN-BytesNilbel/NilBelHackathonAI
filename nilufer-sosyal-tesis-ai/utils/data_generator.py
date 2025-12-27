import pandas as pd
import numpy as np
import os

np.random.seed(42)

# Nilüfer Belediyesi sosyal tesisleri tanımlaması
TESISLER = [
    {"tesis_id": 1, "tesis_tipi": "kütüphane", "kapasite": 180, "isim": "Nilbel Koza Kütüphanesi"},
    {"tesis_id": 2, "tesis_tipi": "kütüphane", "kapasite": 60, "isim": "Şiir Kütüphanesi"},
    {"tesis_id": 3, "tesis_tipi": "kütüphane", "kapasite": 120, "isim": "Akkılıç Kütüphanesi"},
    {"tesis_id": 4, "tesis_tipi": "müze", "kapasite": 100, "isim": "Nilüfer Fotoğraf Müzesi"},
    {"tesis_id": 5, "tesis_tipi": "müze", "kapasite": 70, "isim": "Sağlık Müzesi"},
    {"tesis_id": 6, "tesis_tipi": "müze", "kapasite": 90, "isim": "Edebiyat Müzesi"},
    {"tesis_id": 7, "tesis_tipi": "kafe", "kapasite": 120, "isim": "29 Ekim Kafe"},
    {"tesis_id": 8, "tesis_tipi": "kafe", "kapasite": 90, "isim": "Kafe Pancar"},
    {"tesis_id": 9, "tesis_tipi": "kafe", "kapasite": 150, "isim": "Nilüfer Kent Lokantası"},
    {"tesis_id": 10, "tesis_tipi": "gençlik merkezi", "kapasite": 200, "isim": "Beşevler Gençlik Merkezi"},
    {"tesis_id": 11, "tesis_tipi": "gençlik merkezi", "kapasite": 150, "isim": "Altınşehir Gençlik Merkezi"},
    {"tesis_id": 12, "tesis_tipi": "gençlik merkezi", "kapasite": 130, "isim": "Cumhuriyet Gençlik Merkezi"},
]

def generate_synthetic_data(kayit_sayisi=2000):
    """
    Nilüfer Sosyal Tesis Proje Tanımına (Madde 4.2) uygun veri üretir.
    """
    # 1. Temel Zaman Değişkenleri
    saatler = np.random.randint(9, 22, kayit_sayisi)
    hafta_sonu = np.random.choice([0, 1], kayit_sayisi, p=[0.7, 0.3]) # 1: Hafta sonu
    resmi_tatil = np.random.binomial(1, 0.05, kayit_sayisi) 
    
    # 2. Projeye Özel Değişkenler (Yeni Eklendi)
    sinav_haftasi = np.random.binomial(1, 0.15, kayit_sayisi) # Özellikle kütüphaneleri etkiler
    etkinlik_var = np.random.binomial(1, 0.1, kayit_sayisi)
    rezervasyon_sayisi = np.random.randint(0, 40, kayit_sayisi)

    # 3. Dış Etkenler (Hava Durumu)
    sicaklik = np.random.uniform(0, 35, kayit_sayisi) 
    yagis_var = np.random.binomial(1, 0.2, kayit_sayisi)

    # 4. Tesis ve Kapasite Seçimi
    tesis_ids = np.random.choice([t["tesis_id"] for t in TESISLER], kayit_sayisi)
    kapasiteler = np.array([next(t["kapasite"] for t in TESISLER if t["tesis_id"] == tid) for tid in tesis_ids])

    # 5. Doluluk Oranı Hesaplama Mantığı (Multi-Linear Logic)
    # Modelin öğrenmesi için mantıklı ağırlıklar veriyoruz
    ziyaretci_sayisi = []
    
    for i in range(kayit_sayisi):
        # Baz doluluk (kapasitenin %10-30'u)
        base = kapasiteler[i] * 0.2
        
        # Pozitif Etkiler
        saat_etkisi = (saatler[i] - 9) * 3 if saatler[i] < 16 else (22 - saatler[i]) * 4
        hafta_sonu_etkisi = hafta_sonu[i] * (kapasiteler[i] * 0.25)
        rezervasyon_etkisi = rezervasyon_sayisi[i] * 1.2
        sinav_etkisi = sinav_haftasi[i] * (kapasiteler[i] * 0.3)
        etkinlik_etkisi = etkinlik_var[i] * (kapasiteler[i] * 0.2)
        
        # Negatif Etkiler
        yagis_etkisi = yagis_var[i] * -15
        soguk_etkisi = (10 - sicaklik[i]) * 1.5 if sicaklik[i] < 10 else 0

        # Toplam Hesaplama + Gürültü (Noise)
        toplam = base + saat_etkisi + hafta_sonu_etkisi + rezervasyon_etkisi + \
                 sinav_etkisi + etkinlik_etkisi + yagis_etkisi - soguk_etkisi + \
                 np.random.normal(0, 5)

        # Sınırlandırma
        ziyaretci = max(0, min(int(toplam), kapasiteler[i]))
        ziyaretci_sayisi.append(ziyaretci)

    ziyaretci_sayisi = np.array(ziyaretci_sayisi)
    
    # 6. Hedef Değişken: Doluluk Oranı (Yüzde olarak)
    doluluk_orani = (ziyaretci_sayisi / kapasiteler) * 100

    # DataFrame Oluştur (Train modelin beklediği kolon isimleri ile)
    df = pd.DataFrame({
        "tesis_id": tesis_ids,
        "saat": saatler,
        "hafta_sonu": hafta_sonu,
        "resmi_tatil": resmi_tatil,
        "etkinlik_var": etkinlik_var,
        "sinav_haftasi": sinav_haftasi,
        "rezervasyon_sayisi": rezervasyon_sayisi,
        "sicaklik": sicaklik,
        "yagis_var": yagis_var,
        "ziyaretci_sayisi": ziyaretci_sayisi,
        "doluluk_orani": doluluk_orani
    })

    return df

if __name__ == "__main__":
    df = generate_synthetic_data()
    # Dosya yolunu ekran resmindeki yapıya göre ayarlıyoruz
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "sentetik_ziyaretci.csv")
    
    # Klasör yoksa oluştur
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"--- Nilüfer Projesi Sentetik Verisi Başarıyla Üretildi ---")
    print(f"Kayıt Sayısı: {len(df)}")
    print(f"Dosya Konumu: {output_path}")
    print(df[['saat', 'sinav_haftasi', 'doluluk_orani']].head())
