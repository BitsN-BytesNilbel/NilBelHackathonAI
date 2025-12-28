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
        result = reservation_system.create_reservation(reservation_data)
        if result["status"] == "error": raise HTTPException(status_code=400, detail=result["message"])
        return result
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
