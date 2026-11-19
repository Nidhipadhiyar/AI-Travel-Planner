
def estimate_budget(
    flight_price,
    hotel_price_per_night,
    number_of_nights,
    number_of_days,
    number_of_travellers,
    food_per_person_per_day=800,
    transport_per_person_per_day=300,
    activities_per_person_per_day=500,
    activity_days=None
):
    if number_of_travellers <= 0:
        return {"status": "error", "message": "Number of travellers must be positive."}

    if number_of_nights <= 0 or number_of_days <= 0:
        return {"status": "error", "message": "Number of days and nights must be positive."}

    if activity_days is None:
        activity_days = number_of_days

    if activity_days < 0 or activity_days > number_of_days:
        return {"status": "error", "message": "Activity days must be between 0 and total days."}

    if min(
        flight_price,
        hotel_price_per_night,
        food_per_person_per_day,
        transport_per_person_per_day,
        activities_per_person_per_day
    ) < 0:
        return {"status": "error", "message": "Prices cannot be negative."}

    flight_cost = flight_price * number_of_travellers

    # One hotel room is assumed for the group.
    hotel_cost = hotel_price_per_night * number_of_nights

    # Food and transport are calculated for every travel day.
    food_cost = (
        food_per_person_per_day
        * number_of_travellers
        * number_of_days
    )

    transport_cost = (
        transport_per_person_per_day
        * number_of_travellers
        * number_of_days
    )

    # Activities are calculated only for sightseeing days.
    activities_cost = (
        activities_per_person_per_day
        * number_of_travellers
        * activity_days
    )

    total_cost = (
        flight_cost
        + hotel_cost
        + food_cost
        + transport_cost
        + activities_cost
    )

    return {
        "status": "success",
        "flight_cost": flight_cost,
        "hotel_cost": hotel_cost,
        "food_cost": food_cost,
        "transport_cost": transport_cost,
        "activities_cost": activities_cost,
        "total_cost": total_cost,
        "cost_per_person": round(
            total_cost / number_of_travellers, 2
        )
    }


if __name__ == "__main__":

    print("\n--- BUDGET ESTIMATION TEST ---")

    result = estimate_budget(
        flight_price=5356,
        hotel_price_per_night=1232,
        number_of_nights=3,
        number_of_days=4,
        number_of_travellers=2,
        activity_days=2
    )

    print(result)
