from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List
from pydantic import BaseModel
import sys
import os

# Yolları ayarla
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mevcut importların korunması
from ai.predict import predict_occupancy
from utils.tesisler import TESISLER, get_tesis_by_id
# Sadece kullanılan modülleri import et (performans için)
from utils.datalogger import log_real_data_entry
from utils.smart_ranking import smart_ranking

router = APIRouter()

# ========== TEMEL ENDPOINT'LER ==========

@router.get("/")
def root():
    """API ana sayfası ve bilgi"""
    return {
        "message": "Nilüfer Sosyal Tesis AI API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            "/login - Kullanıcı girişi",
            "/tesisler - Tesis listesi",
            "/tum-tesisler-tahmin - Tüm tesis tahminleri",
            "/log-real-data - Gerçek veri kaydı",
            "/predict - Tek tesis tahmini"
        ]
    }

@router.get("/health")
def health_check():
    """Sistem sağlık kontrolü"""
    return {"status": "healthy", "timestamp": "2025-12-28T02:32:25Z"}

@router.get("/tesisler")
def get_tesisler():
    """Tüm tesislerin listesini döndürür"""
    try:
        return {"tesisler": TESISLER}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tesis listesi alınamadı: {str(e)}")

@router.get("/tum-tesisler-tahmin")
def get_all_predictions():
    """Tüm tesisler için doluluk tahminleri"""
    try:
        predictions = []
        for tesis in TESISLER:
            try:
                prediction = predict_occupancy(tesis["tesis_id"])
                predictions.append({
                    "tesis_adi": tesis["isim"],
                    "tesis_id": tesis["tesis_id"],
                    "doluluk_orani": f"%{prediction.get('doluluk_orani', 'N/A')}",
                    "hava_sicakligi": f"{prediction.get('hava_sicakligi', 'N/A')}°C"
                })
            except Exception as e:
                predictions.append({
                    "tesis_adi": tesis["isim"],
                    "tesis_id": tesis["tesis_id"],
                    "doluluk_orani": "Tahmin edilemedi",
                    "hava_sicakligi": "N/A"
                })

        return {"tahminler": predictions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tahminler alınamadı: {str(e)}")

# ========== GÜVENLİK VE GİRİŞ SİSTEMİ (YENİ) ==========

# Hackathon için örnek kullanıcı veritabanı
USERS = {
    "admin@nilufer.bel.tr": "nilufer16", # Belediye Personeli
    "vatandas@gmail.com": "12345"        # Test Kullanıcısı
}

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginRequest):
    """Kullanıcı girişi ve yetkilendirme"""
    if data.email in USERS and USERS[data.email] == data.password:
        return {
            "status": "success", 
            "message": "Giriş başarılı",
            "role": "admin" if "nilufer" in data.email else "user"
        }
    else:
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")

# ========== GERÇEK VERİ YÖNETİMİ ==========

@router.post("/log-real-data")
def log_real_data_endpoint(data: dict):
    """
    Kullanıcının istediği formatta gerçek veri kaydı
    POST body: {"tesis_id": 1, "doluluk_orani": 75.5}
    """
    try:
        tesis_id = data.get("tesis_id")
        doluluk_orani = data.get("doluluk_orani")

        if tesis_id is None or doluluk_orani is None:
            raise HTTPException(status_code=400, detail="tesis_id ve doluluk_orani gerekli")

        result = log_real_data_entry(tesis_id, doluluk_orani)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gerçek veri log hatası: {str(e)}")

# ========== ANALİZ VE PERFORMANS ==========

@router.get("/retrain")
def trigger_retrain():
    """Gerçek verilerle modeli yeniden eğitir"""
    try:
        from ai.train_model import train_hybrid_model
        result = train_hybrid_model()
        return {"status": "success", "message": "Model yeni verilerle güncellendi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining hatası: {str(e)}")

# ========== VATANDAŞ ODAKLI (WPA) ENDPOINT'LER ==========

@router.get("/akilli-siralama")
def get_smart_ranking(lat: Optional[float] = None, lon: Optional[float] = None, tercih_edilen_tur: Optional[str] = None):
    """Doluluk ve konuma göre en uygun tesisleri önerir"""
    try:
        rankings = smart_ranking.rank_facilities(user_location=(lat, lon) if lat and lon else None, preferred_types=[tercih_edilen_tur] if tercih_edilen_tur else None)
        return {"oneriler": rankings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sıralama hatası: {str(e)}")

@router.post("/rezervasyon-olustur")
def create_reservation_endpoint(reservation_data: dict):
    """Yeni rezervasyon kaydı oluşturur"""
    try:
        # Şimdilik mock response - gerçek implementasyon eksik
        return {
            "status": "success",
            "message": "Rezervasyon oluşturuldu",
            "reservation_id": 12345
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sistem hatası: {str(e)}")

# ========== BELEDİYE YÖNETİM PANELİ ==========

@router.get("/belediye/yuk-dengeleme")
def get_load_balancing():
    """Belediye için tesisler arası yük dengeleme önerileri"""
    try:
        return {"oneriler": smart_ranking.get_load_balancing_recommendations()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict")
def predict(tesis_id: int = 1, rezervasyon: int = 10, sinav_vakti: int = 0):
    """AI doluluk tahmini"""
    try:
        return predict_occupancy(tesis_id, rezervasyon, sinav_vakti)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
