from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router  # 🔥 BU SATIR ŞART

app = FastAPI(
    title="Nilüfer Sosyal Tesis AI API",
    description="Nilüfer Belediyesi sosyal tesis doluluk tahmin API'si",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
