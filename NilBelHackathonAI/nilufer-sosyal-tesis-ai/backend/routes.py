from fastapi import APIRouter
from ai.predict import predict_occupancy

router = APIRouter()

@router.get("/predict")
def predict(tesis_id: int = 1):
    result = predict_occupancy(tesis_id)
    return result
