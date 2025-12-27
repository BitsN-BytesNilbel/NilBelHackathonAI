# Nilüfer Belediyesi Sosyal Tesisleri
# Bu dosya tüm tesis bilgilerini merkezi olarak tutar

TESISLER = [
    {"tesis_id": 1, "tesis_tipi": "kütüphane", "kapasite": 180, "isim": "Nilbel Koza Kütüphanesi"},
    {"tesis_id": 2, "tesis_tipi": "kütüphane", "kapasite": 60, "isim": "Şiir Kütüphanesi"},
    {"tesis_id": 3, "tesis_tipi": "kütüphane", "kapasite": 120, "isim": "Akkılıç Kütüphanesi"},
    {"tesis_id": 4, "tesis_tipi": "müze", "kapasite": 100, "isim": "Nilüfer Fotoğraf Müzesi"},
    {"tesis_id": 5, "tesis_tipi": "müze", "kapasite": 70, "isim": "Sağlık Müzesi"},
    {"tesis_id": 6, "tesis_tipi": "müze", "kapasite": 90, "isim": "Edebiyat Müzesi"},
    {"tesis_id": 7, "tesis_tipi": "kafe", "kapasite": 120, "isim": "29 Ekim Kafe"},
    {"tesis_id": 8, "tesis_tipi": "kafe", "kapasite": 90, "isim": "Kafe Pancar"},
    {"tesis_id": 9, "tesis_tipi": "lokanta", "kapasite": 150, "isim": "Nilüfer Kent Lokantası"},
    {"tesis_id": 10, "tesis_tipi": "gençlik merkezi", "kapasite": 200, "isim": "Beşevler Gençlik Merkezi"},
    {"tesis_id": 11, "tesis_tipi": "gençlik merkezi", "kapasite": 150, "isim": "Altınşehir Gençlik Merkezi"},
    {"tesis_id": 12, "tesis_tipi": "gençlik merkezi", "kapasite": 130, "isim": "Cumhuriyet Gençlik Merkezi"},
]

def get_tesis_by_id(tesis_id):
    """ID'ye göre tesis bilgilerini döndürür"""
    for tesis in TESISLER:
        if tesis["tesis_id"] == tesis_id:
            return tesis
    return None

def get_tesisler_by_tip(tip):
    """Tesis tipine göre tesisleri döndürür"""
    return [t for t in TESISLER if t["tesis_tipi"] == tip]
