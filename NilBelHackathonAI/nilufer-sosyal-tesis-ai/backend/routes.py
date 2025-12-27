from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sys
import os

# Yolları ayarla
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai.predict import predict_occupancy
from utils.tesisler import TESISLER, get_tesis_by_id
from utils.datalogger import log_qr_entry
from utils.data_aggregator import aggregator
from ai.error_tracker import error_tracker

router = APIRouter()

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

@router.get("/predict")
def predict(tesis_id: int = 1, rezervasyon: int = 10, sinav_vakti: int = 0):
    """Geriye uyumluluk için basit tahmin endpoint'i"""
    try:
        result = predict_occupancy(tesis_id, rezervasyon, sinav_vakti)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tahmin hatası: {str(e)}")
