from fastapi import FastAPI
from pydantic import BaseModel
import io
import matplotlib
matplotlib.use("Agg")  # non-interactive backend, required for server-side plotting
import matplotlib.pyplot as plt
from fastapi.responses import StreamingResponse
from rainfall_warning.risk_model import load_artifacts, predict_inundation_risk, get_imd_alert_level


from rainfall_warning.risk_model import load_artifacts, predict_inundation_risk

app = FastAPI(title="Rainfall Early Warning API")

# load once at startup, not on every request — the model and susceptibility
# array are static, so reloading them per-request would be slow and pointless
model, susceptibility, grid_meta = load_artifacts()


class RainfallInput(BaseModel):
    rainfall_mm: float


@app.get("/")
def root():
    return {"status": "ok", "message": "Rainfall Early Warning API is running"}


@app.post("/predict")
def predict(input: RainfallInput):
    imd_alert = get_imd_alert_level(input.rainfall_mm)
    result = predict_inundation_risk(input.rainfall_mm, model, susceptibility)
    return {
        "heavy_rain_alert": result["heavy_rain_alert"],
        "ml_risk_score": result["ml_risk_score"],
        "rainfall_risk": result["rainfall_risk"],
        "grid_bbox": grid_meta["bbox"],
        "grid_shape": grid_meta["shape"],
        "imd_alert_level": imd_alert["level"],
        "imd_alert_label": imd_alert["label"],
        "imd_alert_color": imd_alert["color"],
        # note: we don't return the full inundation_map array here —
        # it's ~15 million numbers, far too large for a JSON response.
        # the dashboard will call a separate endpoint for the map image.
    }

@app.get("/predict/map")
def predict_map(rainfall_mm: float):
    result = predict_inundation_risk(rainfall_mm, model, susceptibility)

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(result["inundation_map"], cmap="YlOrRd", vmin=0, vmax=1)
    ax.set_title(f"Inundation Risk — {rainfall_mm}mm rainfall")
    ax.axis("off")
    fig.colorbar(im, label="Inundation Risk")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")

