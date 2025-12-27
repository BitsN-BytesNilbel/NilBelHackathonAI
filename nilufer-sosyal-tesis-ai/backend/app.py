from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Yolları ayarla
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ai.predict import predict_occupancy
from utils.tesisler import TESISLER

app = FastAPI(
    title="Nilüfer Sosyal Tesis AI API",
    description="Nilüfer Belediyesi sosyal tesis doluluk tahmin API'si",
    version="1.0.0"
)

# CORS ayarları (frontend için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik domainler
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Nilüfer Sosyal Tesis AI API'ye hoş geldiniz"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/tesisler")
def get_tesisler():
    """Tüm tesislerin listesini döndürür"""
    return {
        "tesisler": [
            {
                "id": t["tesis_id"],
                "isim": t["isim"],
                "tip": t["tesis_tipi"],
                "kapasite": t["kapasite"]
            } for t in TESISLER
        ]
    }

@app.get("/tahmin/{tesis_id}")
def get_tahmin(tesis_id: int, rezervasyon: int = 10, sinav_vakti: int = 0):
    """Belirli bir tesis için doluluk tahmini"""
    try:
        sonuc = predict_occupancy(tesis_id, rezervasyon, sinav_vakti)
        return sonuc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tahmin hatası: {str(e)}")

@app.get("/tum-tesisler-tahmin")
def get_tum_tesisler_tahmin(rezervasyon: int = 10, sinav_vakti: int = 0):
    """Tüm tesisler için doluluk tahminleri"""
    try:
        tahminler = []
        for tesis in TESISLER:
            sonuc = predict_occupancy(tesis["tesis_id"], rezervasyon, sinav_vakti)
            tahminler.append({
                "tesis_id": tesis["tesis_id"],
                "tesis_adi": tesis["isim"],
                "doluluk": sonuc["doluluk"],
                "sicaklik": sonuc["sicaklik"]
            })
        return {"tahminler": tahminler}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tahmin hatası: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
