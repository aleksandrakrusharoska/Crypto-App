from fastapi import FastAPI
from app.api import router

app = FastAPI(title="LSTM Prediction Service")
app.include_router(router)

# uvicorn app.main:app --reload --port 8001