from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import model_loader
from pydantic import BaseModel

ml_model = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    ## Runs once on startup before serving requests
    ml_model["data"] = model_loader.load_model()
    yield
    ## Runs once on shutdown when app stops
    ml_model.clear()

app = FastAPI(lifespan=lifespan)

class PredictRequest(BaseModel):
    input: list[float]

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": "data" in ml_model}

@app.post("/predict")
def predict(request: PredictRequest):
    weights = ml_model["data"]["weights"]
    if len(request.input) != len(weights):
        raise HTTPException(status_code=400, detail="Input length must match model weights")

    result = sum(i * w for i, w in zip(request.input, weights))
    
    return {"prediction": result}
