from src.ingest.imd_loader import load_rainfall_data

ds = load_rainfall_data(
    2015,
    "data/raw/rain"
)

print(ds)