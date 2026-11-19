
import requests
from datetime import date, datetime


def get_weather(city, forecast_days=7, start_date=None):

    try:
        # ---------------------------------
        # STEP 1: VALIDATE INPUTS
        # ---------------------------------

        forecast_days = int(forecast_days)

        if forecast_days < 1:
            return {
                "status": "error",
                "message": "Forecast days must be at least 1."
            }

        if start_date is not None:
            start_date = datetime.strptime(
                str(start_date), "%Y-%m-%d"
            ).date()

            today = date.today()

            # Open-Meteo forecast API cannot provide
            # historical weather forecasts.

            if start_date < today:
                return {
                    "status": "date_unavailable",
                    "message": (
                        "Historical weather forecasts are not available "
                        "through this forecast endpoint."
                    )
                }

            days_until_start = (start_date - today).days

            # Open-Meteo forecast endpoint supports
            # a maximum of 16 forecast days.

            required_days = days_until_start + forecast_days

            if required_days > 16:
                return {
                    "status": "date_unavailable",
                    "message": (
                        "The requested travel dates are outside "
                        "the available 16-day weather forecast window."
                    )
                }

        else:
            required_days = min(forecast_days, 16)

        # ---------------------------------
        # STEP 2: FIND CITY COORDINATES
        # ---------------------------------

        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_params = {
            "name": city,
            "count": 10,
            "language": "en",
            "format": "json",
            "countryCode": "IN"
        }

        geo_response = requests.get(
            geo_url,
            params=geo_params,
            timeout=15
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return {
                "status": "not_found",
                "message": f"Location not found: {city}"
            }

        results = geo_data["results"]

        # Prefer an exact city-name match.

        location = next(
            (
                item for item in results
                if item["name"].lower() == city.lower()
            ),
            results[0]
        )

        latitude = location["latitude"]
        longitude = location["longitude"]

        # ---------------------------------
        # STEP 3: GET WEATHER FORECAST
        # ---------------------------------

        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max"
            ],
            "forecast_days": required_days,
            "timezone": "auto"
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=20
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        daily = weather_data["daily"]

        # ---------------------------------
        # STEP 4: FILTER TRAVEL DATES
        # ---------------------------------

        forecast = []

        for i in range(len(daily["time"])):

            forecast_date = datetime.strptime(
                daily["time"][i], "%Y-%m-%d"
            ).date()

            # If a travel start date is provided,
            # include only the requested trip dates.

            if start_date is not None:

                end_date = date.fromordinal(
                    start_date.toordinal() + forecast_days - 1
                )

                if not (start_date <= forecast_date <= end_date):
                    continue

            forecast.append({
                "date": daily["time"][i],
                "weather_code": daily["weather_code"][i],
                "max_temperature": daily["temperature_2m_max"][i],
                "min_temperature": daily["temperature_2m_min"][i],
                "rain_probability": daily[
                    "precipitation_probability_max"
                ][i]
            })

        if not forecast:
            return {
                "status": "date_unavailable",
                "message": "No weather forecast is available for the requested dates."
            }

        # ---------------------------------
        # STEP 5: RETURN WEATHER RESULTS
        # ---------------------------------

        return {
            "status": "success",
            "city": location["name"],
            "forecast": forecast
        }

    except requests.exceptions.RequestException as error:

        return {
            "status": "weather_unavailable",
            "message": str(error)
        }

    except (KeyError, TypeError, ValueError) as error:

        return {
            "status": "weather_unavailable",
            "message": f"Unexpected weather response: {error}"
        }


# ---------------------------------
# TEST THE WEATHER FUNCTION
# ---------------------------------

if __name__ == "__main__":

    print("\n--- WEATHER TEST ---")

    result = get_weather(
        city="Mumbai",
        forecast_days=4,
        start_date="2026-11-18"
    )

    print(result)
