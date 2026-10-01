from src.preprocess.rainfall_processing import process_rainfall

process_rainfall(
    input_folder="data/raw/rain",
    output_file="data/processed/periyar_rainfall_features.csv"
)