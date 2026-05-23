from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import customers, explanations, metrics, predictions

app = FastAPI(
    title="Churn Prediction Model Comparison API",
    description="Mock API for comparing TFT, NHiTS, and TabNet churn prediction models.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router)
app.include_router(customers.router)
app.include_router(predictions.router)
app.include_router(explanations.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
