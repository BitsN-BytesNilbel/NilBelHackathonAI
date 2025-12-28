from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import sys
import os
from datetime import datetime # EKLEME: Zaman verisi için

# Yolları ayarla
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai.predict import predict_occupancy
from utils.tesisler import TESISLER, get_tesis_by_id
from utils.datalogger import log_qr_entry
from utils.data_aggregator import aggregator
from ai.error_tracker import error_tracker
from utils.smart_ranking import smart_ranking
from utils.events import event_manager
from utils.reservations import reservation_system

router = APIRouter()

# QR Giriş isteği için veri modeli
class QRRequest(BaseModel):
    user_id: str
    tesis_id: int

# ========== GÜNCELLENEN QR GİRİŞ VE AI VERİ AKTARIM NOKTASI ==========

@router.post("/qr/entry")
async def qr_entry(request: QRRequest):
    """
    Vatandaş QR okuttuğunda FEATURES listesini toplar ve AI birimine aktarır.
    """
    try:
        # 1. Anlık zaman verilerini al
        simdi = datetime.now()
        
        # 2. Hava durumu ve mevcut tahmin verilerini çek (AI Modülünden)
        # predict_occupancy fonksiyonunu anlık durum fotoğrafı çekmek için kullanıyoruz
        mevcut_durum = predict_occupancy(request.tesis_id)
        
        # 3. Talep edilen FEATURES setini oluştur
        ai_feature_set = {
            "tesis_id": request.tesis_id,
            "saat": simdi.hour,
            "hafta_sonu": 1 if simdi.weekday() >= 5 else 0,
            "resmi_tatil": 0, # Takvim modülü entegrasyonu için placeholder
            "etkinlik_var": 1 if event_manager.get_active_events() else 0,
            "sinav_haftasi": 0, # Sistem takviminden çekilebilir
            "rezervasyon_sayisi": len(reservation_system.get_user_reservations(request.user_id)),
            "sicaklik": mevcut_durum.get("sicaklik", 20),
            "yagis_var": 1 if "Yağmur" in mevcut_durum.get("durum", "") else 0,
            "target_doluluk": 1.0 # Giriş yapıldığı an için hedeflenen doluluk etiketi
        }

        # 4. Veriyi AI Birimine (Datalogger) Aktar
        # AI arkadaşının yazdığı log_qr_entry bu sözlüğü alıp CSV/DB'ye yazar
        log_qr_entry(request.tesis_id, ai_feature_set)

        return {
            "status": "success", 
            "message": f"{request.tesis_id} nolu tesise giriş başarılı. AI verisi kaydedildi.",
            "kaydedilen_ozellikler": ai_feature_set
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR AI Aktarım Hatası: {str(e)}")

# ========== MEVCUT FONKSİYONLAR (DEĞİŞTİRİLMEDİ) ==========

@router.post("/qr-log")
def log_qr_data(tesis_id: int, doluluk_orani: float, rezervasyon: Optional[int] = 0):
    try:
        result = log_qr_entry(tesis_id, {"doluluk_orani": doluluk_orani, "rezervasyon": rezervasyon})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR log hatası: {str(e)}")

@router.get("/akilli-siralama")
def get_smart_ranking(lat: Optional[float] = None, lon: Optional[float] = None, tercih_edilen_tur: Optional[str] = None, top_n: int = 5):
    try:
        user_location = (lat, lon) if lat and lon else None
        preferred_types = [tercih_edilen_tur] if tercih_edilen_tur else None
        rankings = smart_ranking.rank_facilities(user_location=user_location, preferred_types=preferred_types, top_n=top_n)
        result = []
        for rank in rankings:
            result.append({
                "sira": len(result) + 1,
                "tesis_id": rank["tesis"]["tesis_id"],
                "tesis_adi": rank["tesis"]["isim"],
                "tesis_tipi": rank["tesis"]["tesis_tipi"],
                "doluluk_orani": rank["prediction"]["doluluk"],
                "hava_sicakligi": rank["prediction"]["sicaklik"],
                "siralama_nedeni": rank["rank_reason"],
                "kapasite": rank["tesis"]["kapasite"]
            })
        return {"oneriler": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Akıllı sıralama hatası: {str(e)}")

@router.get("/tesisler")
def get_all_facilities():
    try:
        return TESISLER
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tesis listesi hatası: {str(e)}")

@router.get("/tum-tesisler-tahmin")
def get_all_predictions():
    try:
        results = []
        for tesis in TESISLER:
            try:
                prediction = predict_occupancy(tesis["tesis_id"], rezervasyon=10, sinav_vakti=0)
                results.append({
                    "tesis_id": tesis["tesis_id"],
                    "isim": tesis["isim"],
                    "doluluk_orani": prediction.get("doluluk", 0.5),
                    "durum": prediction.get("durum", "Müsait"),
                    "sicaklik": prediction.get("sicaklik", 20)
                })
            except Exception as inner_e:
                results.append({
                    "tesis_id": tesis["tesis_id"],
                    "isim": tesis["isim"],
                    "doluluk_orani": 0.0,
                    "durum": "Hata",
                    "sicaklik": 0
                })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Toplu tahmin ana hatası: {str(e)}")