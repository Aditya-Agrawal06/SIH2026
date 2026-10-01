import json
from pathlib import Path

import joblib
import numpy as np

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def load_artifacts():
    model = joblib.load(MODELS_DIR / "rainfall_lgbm.pkl")
    susceptibility = np.load(DATA_DIR / "periyar_susceptibility.npy")
    with open(DATA_DIR / "periyar_grid_meta.json") as f:
        grid_meta = json.load(f)
    return model, susceptibility, grid_meta


def predict_inundation_risk(rainfall_today_mm: float, model, susceptibility: np.ndarray) -> dict:
    heavy_rain_alert = int(rainfall_today_mm >= 64.5)

    feature_row = [[
        rainfall_today_mm,
        rainfall_today_mm * 3,
        rainfall_today_mm * 7,
        rainfall_today_mm * 15,
        rainfall_today_mm,
        rainfall_today_mm,
        rainfall_today_mm,
    ]]

    ml_risk_score = model.predict_proba(feature_row)[:, 1][0]
    rainfall_risk = max(heavy_rain_alert, ml_risk_score)
    inundation_map = rainfall_risk * susceptibility

    return {
        "heavy_rain_alert": heavy_rain_alert,
        "ml_risk_score": float(ml_risk_score),
        "rainfall_risk": float(rainfall_risk),
        "inundation_map": inundation_map,
    }

def get_imd_alert_level(rainfall_mm: float) -> dict:
    if rainfall_mm < 64:
        return {"level": "Green", "label": "No Warning", "color": "#2ecc71"}
    elif rainfall_mm < 115.6:
        return {"level": "Yellow", "label": "Be Aware", "color": "#f1c40f"}
    elif rainfall_mm < 204.5:
        return {"level": "Orange", "label": "Be Prepared", "color": "#e67e22"}
    else:
        return {"level": "Red", "label": "Take Action", "color": "#e74c3c"}