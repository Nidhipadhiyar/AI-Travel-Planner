
import sys
from pathlib import Path

import pandas as pd


# ---------------------------------
# PROJECT PATH AND DATA LOADING
# ---------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.data_loader import load_datasets


flights_df, hotels_df, places_df = load_datasets()


# ---------------------------------
# 1. FLIGHT SEARCH
# ---------------------------------

def search_flights(source, destination, travel_date=None, max_budget=None):

    results = flights_df[
        (flights_df["from"].str.lower() == source.lower()) &
        (flights_df["to"].str.lower() == destination.lower())
    ].copy()

    # Check whether flights exist for this route

    if results.empty:
        return {
            "status": "not_found",
            "message": f"No flights available from {source} to {destination}."
        }

    # Filter flights by intended travel date

    if travel_date is not None:

        requested_date = pd.to_datetime(travel_date).date()

        results["departure_date"] = pd.to_datetime(
            results["departure_time"]
        ).dt.date

        results = results[
            results["departure_date"] == requested_date
        ]

        if results.empty:
            return {
                "status": "date_unavailable",
                "message": (
                    f"No sample flight found from {source} to {destination} "
                    f"on {requested_date}. The dataset contains historical "
                    "sample flight records only."
                )
            }

        results = results.drop(columns=["departure_date"])

    # Filter flights by budget

    if max_budget is not None:

        results = results[
            results["price"] <= max_budget
        ]

        if results.empty:
            return {
                "status": "budget_exceeded",
                "message": f"No flights found within ₹{max_budget}."
            }

    # Sort flights by price

    results = results.sort_values(
        by="price",
        ascending=True
    )

    return {
        "status": "success",
        "flights": results.to_dict(orient="records")
    }


# ---------------------------------
# 2. HOTEL SEARCH
# ---------------------------------

def search_hotels(
    city,
    max_budget=None,
    min_stars=None,
    required_amenities=None
):

    results = hotels_df[
        hotels_df["city"].str.lower() == city.lower()
    ].copy()

    # Check whether hotels exist in the city

    if results.empty:
        return {
            "status": "not_found",
            "message": f"No hotels available in {city}."
        }

    # Filter by maximum price per night

    if max_budget is not None:

        results = results[
            results["price_per_night"] <= max_budget
        ]

    # Filter by minimum star rating

    if min_stars is not None:

        results = results[
            results["stars"] >= min_stars
        ]

    # Filter by required amenities

    if required_amenities:

        required = [
            amenity.lower()
            for amenity in required_amenities
        ]

        results = results[
            results["amenities"].apply(
                lambda amenities: all(
                    item in [a.lower() for a in amenities]
                    for item in required
                )
            )
        ]

    # Check whether matching hotels exist

    if results.empty:
        return {
            "status": "no_match",
            "message": "No hotels match the selected preferences."
        }

    # Sort hotels by price

    results = results.sort_values(
        by="price_per_night",
        ascending=True
    )

    return {
        "status": "success",
        "hotels": results.to_dict(orient="records")
    }


# ---------------------------------
# 3. PLACES SEARCH
# ---------------------------------

def search_places(city, category=None, min_rating=None):

    results = places_df[
        places_df["city"].str.lower() == city.lower()
    ].copy()

    # Check whether places exist in the city

    if results.empty:
        return {
            "status": "not_found",
            "message": f"No places available in {city}."
        }

    # Filter by attraction category

    if category is not None:

        results = results[
            results["type"].str.lower() == category.lower()
        ]

    # Filter by minimum rating

    if min_rating is not None:

        results = results[
            results["rating"] >= min_rating
        ]

    # Check whether matching places exist

    if results.empty:
        return {
            "status": "no_match",
            "message": "No places match your preferences."
        }

    # Sort places by rating

    results = results.sort_values(
        by="rating",
        ascending=False
    )

    return {
        "status": "success",
        "places": results.to_dict(orient="records")
    }


# ---------------------------------
# TEST THE FUNCTIONS
# ---------------------------------

if __name__ == "__main__":

    print("\nFLIGHT SEARCH TEST")
    print("------------------------------")

    print(
        search_flights(
            source="Goa",
            destination="Mumbai",
            travel_date="2026-11-18"
        )
    )

    print("\nHOTEL SEARCH TEST")
    print("------------------------------")

    print(
        search_hotels(
            city="Goa",
            max_budget=3000
        )
    )

    print("\nPLACES SEARCH TEST")
    print("------------------------------")

    print(
        search_places(
            city="Mumbai"
        )
    )
