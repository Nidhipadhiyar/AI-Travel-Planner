
import json
from pathlib import Path

import pandas as pd


# Find the main project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Dataset directory
DATA_DIR = BASE_DIR / "data"


def load_datasets():
    """Load all three travel datasets."""

    with open(DATA_DIR / "flights.json", "r", encoding="utf-8") as file:
        flights = json.load(file)

    with open(DATA_DIR / "hotels.json", "r", encoding="utf-8") as file:
        hotels = json.load(file)

    with open(DATA_DIR / "places.json", "r", encoding="utf-8") as file:
        places = json.load(file)

    flights_df = pd.DataFrame(flights)
    hotels_df = pd.DataFrame(hotels)
    places_df = pd.DataFrame(places)

    return flights_df, hotels_df, places_df


if __name__ == "__main__":
    flights_df, hotels_df, places_df = load_datasets()

    print("Datasets loaded successfully!")
    print("Flights:", flights_df.shape)
    print("Hotels:", hotels_df.shape)
    print("Places:", places_df.shape)
