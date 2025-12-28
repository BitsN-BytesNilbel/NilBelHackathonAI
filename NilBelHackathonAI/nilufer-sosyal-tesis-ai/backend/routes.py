from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import sys
import os
from datetime import datetime # EKLEME: Zaman verisi için

# Login için model
class LoginRequest(BaseModel):
    username: str
    password: str

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

# Login endpoint
@router.post("/login")
async def login(request: LoginRequest):
    # Belirtilen giriş bilgileri kontrolü
    valid_credentials = {
        "vatandas@gmail.com": "12345",
        "admin@nilufer.bel.tr": "nilufer16"
    }

    if request.username in valid_credentials and request.password == valid_credentials[request.username]:
        return {"status": "success", "message": "Giriş başarılı", "user_id": request.username}
    else:
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre")

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
                # Doluluk oranını güvenli şekilde parse et
                doluluk_str = prediction.get("doluluk", "0%")
                doluluk_orani = float(doluluk_str.replace('%', '')) / 100.0 if '%' in doluluk_str else 0.0
                results.append({
                    "tesis_id": tesis["tesis_id"],
                    "isim": tesis["isim"],
                    "doluluk_orani": doluluk_orani,
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

# ========== REZERVASYON ENDPOINTLERİ ==========

class ReservationRequest(BaseModel):
    user_id: str
    tesis_id: int
    tarih: str
    saat: int
    sure: int = 2  # Default 2 saat
    kisi_sayisi: int = 1  # Default 1 kişi

@router.post("/rezervasyon-olustur")
async def create_reservation_endpoint(request: ReservationRequest):
    try:
        user_data = {
            "user_id": request.user_id,
            "tesis_id": request.tesis_id,
            "tarih": request.tarih,
            "saat": request.saat,
            "sure": request.sure,
            "kisi_sayisi": request.kisi_sayisi
        }

        result = reservation_system.create_reservation(user_data)
        if result["status"] == "success":
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rezervasyon oluşturma hatası: {str(e)}")

@router.get("/rezervasyonlarim/{user_id}")
async def get_user_reservations_endpoint(user_id: str):
    try:
        reservations = reservation_system.get_user_reservations(user_id)
        return {"rezervasyonlar": reservations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rezervasyon getirme hatası: {str(e)}")

# ========== BELEDİYE YÖNETİM ENDPOINTLERİ ==========

@router.get("/belediye/tum-rezervasyonlar")
async def get_all_reservations():
    try:
        # Tüm rezervasyonları döndür
        all_reservations = []
        for user in set(r["user_id"] for r in reservation_system.reservations):
            user_res = reservation_system.get_user_reservations(user)
            all_reservations.extend(user_res)
        return {"tum_rezervasyonlar": all_reservations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tüm rezervasyonları getirme hatası: {str(e)}")

@router.get("/belediye/istatistikler")
async def get_reservation_stats():
    try:
        stats = reservation_system.get_reservation_stats()
        return {"istatistikler": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İstatistik getirme hatası: {str(e)}")

@router.get("/belediye/yuk-dengeleme")
async def get_load_balancing_analysis():
    try:
        # Basit yük dengeleme analizi: tesislerin doluluk oranlarına göre
        from utils.tesisler import TESISLER
        analysis = []
        for tesis in TESISLER:
            prediction = predict_occupancy(tesis["tesis_id"])
            analysis.append({
                "tesis_id": tesis["tesis_id"],
                "tesis_adi": tesis["isim"],
                "doluluk_orani": prediction.get("doluluk", 0.5),
                "durum": prediction.get("durum", "Bilinmiyor"),
                "oneri": "Yüksek doluluk" if prediction.get("doluluk", 0) > 0.8 else "Normal"
            })
        return {"yuk_dengeleme_analizi": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yük dengeleme analizi hatası: {str(e)}")

@router.get("/belediye/performans-raporu")
async def get_performance_report():
    try:
        # Performans raporu: genel sistem durumu
        report = {
            "toplam_tesis": len(TESISLER),
            "toplam_rezervasyon": len(reservation_system.reservations),
            "aktif_rezervasyon": len([r for r in reservation_system.reservations if r["durum"] == "aktif"]),
            "sistem_durumu": "Çalışıyor",
            "son_guncelleme": datetime.now().isoformat()
        }
        return {"performans_raporu": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performans raporu hatası: {str(e)}")

@router.post("/belediye/model-egitim")
async def retrain_model():
    try:
        # Model yeniden eğitimi simülasyonu
        # Gerçekte train_model.py'yi çalıştırır
        import subprocess
        result = subprocess.run(["python", "ai/train_model.py"], capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "success", "message": "Model yeniden eğitildi"}
        else:
            raise HTTPException(status_code=500, detail=f"Model eğitimi başarısız: {result.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model eğitimi hatası: {str(e)}")

@router.get("/belediye/gunluk-istatistikler")
async def get_daily_stats():
    try:
        # Günlük istatistikler: basit örnek
        today = datetime.now().date()
        today_reservations = [r for r in reservation_system.reservations if r["tarih"] == str(today)]
        stats = {
            "tarih": str(today),
            "gunluk_rezervasyon": len(today_reservations),
            "gunluk_giris": 0,  # QR giriş loglarından hesaplanabilir
            "en_populer_tesis": "Tesis 1"  # Basit örnek
        }
        return {"gunluk_istatistikler": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Günlük istatistik hatası: {str(e)}")

@router.get("/belediye/tesis-qr-yonetimi")
async def get_facility_qr_management():
    try:
        # Tesis QR yönetimi: her tesis için QR kod bilgisi
        qr_info = []
        for tesis in TESISLER:
            qr_info.append({
                "tesis_id": tesis["tesis_id"],
                "tesis_adi": tesis["isim"],
                "qr_kod": f"QR_{tesis['tesis_id']}",
                "aktif": True
            })
        return {"tesis_qr_yonetimi": qr_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tesis QR yönetimi hatası: {str(e)}")
