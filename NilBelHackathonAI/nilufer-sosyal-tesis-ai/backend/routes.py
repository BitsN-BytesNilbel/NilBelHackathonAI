from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import sys
import os
from datetime import datetime, timedelta

# Yolları ayarla
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mevcut importlar
from ai.predict import predict_occupancy
from utils.tesisler import TESISLER, get_tesis_by_id
from utils.datalogger import log_qr_entry
from utils.data_aggregator import aggregator
from ai.error_tracker import error_tracker
from utils.smart_ranking import smart_ranking
from utils.events import event_manager
from utils.reservations import reservation_system

# YENİ: Veritabanı kontrol fonksiyonu (database.py dosyasından)
from database import check_and_log_entry 

router = APIRouter()

# ========== YENİ: QR GİRİŞ MODELLERİ VE ENDPOINT'LERİ ==========

class QRRequest(BaseModel):
    user_id: str
    tesis_id: int

@router.post("/qr/entry")
async def qr_entry(request: QRRequest):
    """
    Vatandaş QR okuttuğunda çalışan ana endpoint. 
    1.5 saat (90 dk) kuralını denetler ve girişi veritabanına işler.
    """
    try:
        # 1. Veritabanından 1.5 saatlik zaman kilidi kontrolü yapılır
        # Mantık: t_simdi - t_son_giris >= 90 dk
        success, message = check_and_log_entry(request.user_id, request.tesis_id)
        
        if not success:
            return {"status": "error", "message": message}
        
        # 2. Giriş başarılıysa AI modelini beslemek için loglama yapılır
        log_qr_entry(request.tesis_id, {
            "doluluk_orani": 1.0, 
            "user_action": "entry",
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "success", "message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR işlem hatası: {str(e)}")

# ========== MEVCUT QR LOG FONKSİYONLARI (KORUNDU) ==========

@router.post("/qr-log")
def log_qr_data(tesis_id: int, doluluk_orani: float, rezervasyon: Optional[int] = 0):
    """QR kod okuma verisini kaydeder"""
    try:
        result = log_qr_entry(tesis_id, {"doluluk_orani": doluluk_orani, "rezervasyon": rezervasyon})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QR log hatası: {str(e)}")

@router.post("/qr-batch")
def log_qr_batch(qr_data: list):
    """Çoklu QR verisini işler ve kaydeder"""
    try:
        results = []
        for item in qr_data:
            result = log_qr_entry(
                item["tesis_id"],
                {
                    "doluluk_orani": item["doluluk_orani"],
                    "rezervasyon": item.get("rezervasyon", 0)
                }
            )
            results.append(result)

        return {"processed": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch QR log hatası: {str(e)}")

# ========== PERFORMANS VE ANALİZ (KORUNDU) ==========

@router.get("/performance")
def get_model_performance():
    """Model performans raporunu döndürür"""
    try:
        report = error_tracker.generate_performance_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performans raporu hatası: {str(e)}")

@router.get("/error-trends")
def get_error_trends(days: int = 7):
    """Hata trendlerini döndürür"""
    try:
        trends = error_tracker.get_error_trends(days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hata trendleri hatası: {str(e)}")

@router.get("/retrain")
def trigger_retrain():
    """Manuel model yeniden eğitimi tetikler"""
    try:
        from ai.train_model import train_hybrid_model
        result = train_hybrid_model()
        return {"status": "success", "message": "Model yeniden eğitildi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining hatası: {str(e)}")

@router.get("/data-stats")
def get_data_stats():
    """Veri istatistiklerini döndürür"""
    try:
        from utils.datalogger import data_logger
        stats = {
            "gercek_veri_kayitlari": data_logger.get_record_count(),
            "sentetik_veri_dosyasi": os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "sentetik_ziyaretci.csv")),
            "model_dosyasi": os.path.exists(os.path.join(os.path.dirname(__file__), "..", "ai", "model.pkl")),
            "hata_log_dosyasi": os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "model_errors.json"))
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veri istatistikleri hatası: {str(e)}")

# ========== YENİ WPA ENDPOINT'LERİ (KORUNDU) ==========

@router.get("/akilli-siralama")
def get_smart_ranking(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    tercih_edilen_tur: Optional[str] = None,
    top_n: int = 5
):
    """Akıllı tesis sıralaması - Vatandaşlar için"""
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

@router.get("/etkinlikler")
def get_events(date: Optional[str] = None, days: int = 7):
    """Etkinlik listesi"""
    try:
        events = event_manager.get_active_events(date) if date else event_manager.get_upcoming_events(days)
        return {"count": len(events), "etkinlikler": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Etkinlik hatası: {str(e)}")

@router.post("/rezervasyon-olustur")
def create_reservation_endpoint(reservation_data: dict):
    """Rezervasyon oluşturma"""
    try:
        result = reservation_system.create_reservation(reservation_data)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rezervasyon hatası: {str(e)}")

@router.delete("/rezervasyon-iptal/{reservation_id}")
def cancel_reservation_endpoint(reservation_id: str, user_id: str):
    """Rezervasyon iptali"""
    try:
        result = reservation_system.cancel_reservation(reservation_id, user_id)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rezervasyon iptal hatası: {str(e)}")

@router.get("/rezervasyonlarim/{user_id}")
def get_user_reservations(user_id: str):
    """Kullanıcının rezervasyonları"""
    try:
        reservations = reservation_system.get_user_reservations(user_id)
        return {"rezervasyonlar": reservations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rezervasyon listesi hatası: {str(e)}")

# ========== BELEDİYE YÖNETİM PANELİ (KORUNDU) ==========

@router.get("/belediye/yuk-dengeleme")
def get_load_balancing():
    """Belediye için yük dengeleme önerileri"""
    try:
        recommendations = smart_ranking.get_load_balancing_recommendations()
        return {"oneriler": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yük dengeleme hatası: {str(e)}")

@router.get("/belediye/istatistikler")
def get_municipality_stats():
    """Belediye için kapsamlı istatistikler"""
    try:
        total_capacity = sum(t["kapasite"] for t in TESISLER)
        reservation_stats = reservation_system.get_reservation_stats()
        performance = error_tracker.generate_performance_report()
        return {
            "tesis_bilgileri": {
                "toplam_tesis": len(TESISLER),
                "toplam_kapasite": total_capacity,
                "tesis_tipleri": list(set(t["tesis_tipi"] for t in TESISLER))
            },
            "rezervasyon_istatistikleri": reservation_stats,
            "model_performans": performance,
            "etkinlik_sayisi": len(event_manager.get_active_events())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Belediye istatistikleri hatası: {str(e)}")

@router.get("/predict")
def predict(tesis_id: int = 1, rezervasyon: int = 10, sinav_vakti: int = 0):
    """Geriye uyumluluk için basit tahmin endpoint'i"""
    try:
        result = predict_occupancy(tesis_id, rezervasyon, sinav_vakti)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tahmin hatası: {str(e)}")