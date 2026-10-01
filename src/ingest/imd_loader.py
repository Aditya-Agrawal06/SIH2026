import imdlib


def load_rainfall_data(year, input_folder):
    data = imdlib.open_data(
        "rain",
        year,
        year,
        "yearwise",
        input_folder
    )

    return data.get_xarray()