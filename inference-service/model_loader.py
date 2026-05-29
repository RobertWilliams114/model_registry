import json
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "model.json"

def load_model():
    with open(MODEL_PATH, "r") as file:
        return json.load(file)

