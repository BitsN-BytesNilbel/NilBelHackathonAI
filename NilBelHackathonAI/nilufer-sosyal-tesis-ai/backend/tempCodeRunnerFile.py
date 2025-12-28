from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router  # 🔥 BU SATIR ŞART

app = FastAPI(
    title="Nilüfer Sosyal Tesis AI API",
    description="Nilüfer Belediyesi sosyal tesis doluluk tahmin ve yönetim sistemi",
    version="1.0.0"
)

# CORS Ayarları: Frontend (Kişi 3) localhost:3000 vb. farklı porttan geleceği için bu şart.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Güvenlik için hackathon sonrası spesifik domain girilmeli
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)