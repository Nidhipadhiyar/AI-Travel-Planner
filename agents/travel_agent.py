
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# --------------------------------------------------
# 1. PROJECT PATH AND ENVIRONMENT SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not found. Please check your .env file."
    )

# --------------------------------------------------
# 2. IMPORT PROJECT FUNCTIONS
# --------------------------------------------------

from tools.travel_tools import (
    search_flights,
    search_hotels,
    search_places
)

from tools.weather_tool import get_weather

from tools.budget_tool import estimate_budget


# --------------------------------------------------
# 3. INITIALIZE GEMINI MODEL
# --------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=GOOGLE_API_KEY,
)


# --------------------------------------------------
# 4. DEFINE AGENT TOOLS
# --------------------------------------------------

@tool
def flight_search(
    source_city: str,
    destination_city: str,
    travel_date: str
):
    """
    Search sample flights between two cities on the
    requested travel date.

    Returns matching flights or explains when flights
    are unavailable for the requested date.

    The dataset contains historical sample records,
    not live flight availability.
    """

    return search_flights(
        source=source_city,
        destination=destination_city,
        travel_date=travel_date
    )


@tool
def hotel_search(
    city: str,
    max_budget: int = None,
    min_stars: int = None
):
    """
    Search hotels in a destination city.

    Filters hotels according to the nightly budget
    and minimum star rating.

    Returns matching hotels sorted by price, with
    the cheapest matching hotel first.
    """

    result = search_hotels(
        city=city,
        max_budget=max_budget,
        min_stars=min_stars
    )

    if result.get("status") == "success":

        hotels = result["hotels"]

        return {
            "status": "success",
            "cheapest_hotel": hotels[0],
            "all_matching_hotels": hotels
        }

    return result


@tool
def places_search(
    city: str,
    category: str = None,
    min_rating: float = None
):
    """
    Discover places and attractions in a destination city.

    Optional filters include attraction category
    and minimum rating.

    Returns only places available in the dataset.
    """

    return search_places(
        city=city,
        category=category,
        min_rating=min_rating
    )


@tool
def weather_lookup(
    city: str,
    forecast_days: int,
    start_date: str
):
    """
    Get weather forecasts for the destination city
    on the user's intended travel dates.

    Returns daily weather information including
    minimum temperature, maximum temperature,
    and rain probability.

    Weather forecasts are subject to the available
    Open-Meteo forecast window.
    """

    return get_weather(
        city=city,
        forecast_days=forecast_days,
        start_date=start_date
    )



@tool
def budget_estimation(
    flight_price: float,
    hotel_price_per_night: float,
    number_of_nights: int,
    number_of_days: int,
    number_of_travellers: int,
    activity_days: int,
    food_per_person_per_day: float = 800,
    transport_per_person_per_day: float = 300,
    activities_per_person_per_day: float = 500
):
    """
    Estimate the total trip budget.

    Calculates flight, hotel, food, transport,
    and activities costs.

    Hotel cost assumes one room for the group.
    Flight price is multiplied by the number of travellers.
    Food and transport are calculated for all travel days.
    Activities are calculated only for sightseeing days.
    """

    return estimate_budget(
        flight_price=flight_price,
        hotel_price_per_night=hotel_price_per_night,
        number_of_nights=number_of_nights,
        number_of_days=number_of_days,
        number_of_travellers=number_of_travellers,
        activity_days=activity_days,
        food_per_person_per_day=food_per_person_per_day,
        transport_per_person_per_day=transport_per_person_per_day,
        activities_per_person_per_day=activities_per_person_per_day
    )



# --------------------------------------------------
# 5. REGISTER ALL TOOLS
# --------------------------------------------------

travel_tools = [
    flight_search,
    hotel_search,
    places_search,
    weather_lookup,
    budget_estimation
]


# --------------------------------------------------
# 6. AGENT SYSTEM PROMPT
# --------------------------------------------------


SYSTEM_PROMPT = """
You are an intelligent Agentic AI Travel Planning Assistant.

Your responsibility is to create personalized, practical,
and data-supported travel plans using the available tools.

You must make decisions based on tool results.
Never invent travel information, prices, or availability.

--------------------------------------------------
A. UNDERSTAND THE USER REQUEST
--------------------------------------------------

Identify the following information:

1. Source city
2. Destination city
3. Travel start date
4. Travel end date
5. Number of travel days
6. Number of travellers
7. Hotel budget per night
8. Other travel preferences, if provided

If essential information is missing, ask the user
for clarification instead of making unsupported assumptions.

--------------------------------------------------
B. FLIGHT SEARCH RULES
--------------------------------------------------

1. Use flight_search with the exact source city,
   destination city, and requested travel date.

2. Never recommend a flight from a different date.

3. Only display flight details returned by the tool.

4. If no flight is available, clearly state that
   no matching sample flight was found.

5. Flight records are historical sample data,
   not live booking availability.

6. Do not invent return-flight information.
   If return-flight data is unavailable, say so.

7. If no flight fare is available, use zero only
   as an input to the budget calculation and clearly
   disclose that flight expenses are excluded.

--------------------------------------------------
C. HOTEL SEARCH RULES
--------------------------------------------------

1. Use hotel_search for the destination city.

2. Apply the user's nightly hotel budget.

3. Select the cheapest matching hotel unless
   the user has specified another preference.

4. Display the actual hotel name, ID, star rating,
   nightly price, and amenities returned by the tool.

5. Never invent hotel facilities or prices.

6. If no matching hotel is available, explain this
   instead of recommending an unsupported hotel.

--------------------------------------------------
D. PLACES AND ATTRACTIONS
--------------------------------------------------

1. Use places_search to retrieve destination attractions.

2. Recommend only attractions returned by the tool.

3. Preserve each attraction's name, category,
   and rating exactly as provided.

4. Do not invent descriptions, addresses, opening hours,
   travel distances, or geographical locations.

5. Do not assume attractions are close to one another.

6. Do not invent activities such as shopping,
   swimming, or local experiences unless supported
   by the available data.

7. Do not assume that hotel facilities will be used.

8. If attraction categories are unusual or inconsistent,
   clearly mention that the dataset needs verification.

9. If there are insufficient attractions, leave
   some itinerary time free rather than inventing activities.

--------------------------------------------------
E. DAY-WISE ITINERARY RULES
--------------------------------------------------

1. The itinerary must match the requested travel dates.

2. Day 1 is the arrival day. Keep activities light.

3. Schedule the main sightseeing activities between
   Day 2 and the day before departure.

4. The final day is the departure day.

5. Do not schedule sightseeing on the departure day
   unless the user explicitly requests it or provides
   sufficient time for activities.

6. Distribute available attractions across the trip
   without repeating them.

7. Do not force attractions into every day.

8. If there are not enough attractions for all days,
   leave free time instead of inventing activities.

9. Do not claim that a traveller can visit multiple
   attractions within a particular time or distance
   unless that information is available.

10. Clearly distinguish suggested visits from
    confirmed bookings or reservations.

--------------------------------------------------
F. WEATHER FORECAST RULES
--------------------------------------------------

1. Use weather_lookup for the destination city.

2. Pass the exact travel start date and number
   of trip days to the tool.

3. Display only weather dates falling within
   the requested travel period.

4. Include maximum temperature, minimum temperature,
   and rain probability when available.

5. If the requested dates are outside the available
   forecast window, clearly state that weather
   information is unavailable.

6. Never invent weather information.

7. Do not present today's weather as the weather
   for a future travel date.

--------------------------------------------------
G. BUDGET ESTIMATION RULES
--------------------------------------------------

1. Use budget_estimation to calculate the trip cost.

2. Use the actual selected hotel price.

3. Use the actual flight fare only when a matching
   flight is available.

4. Calculate the number of nights correctly.
   Normally, nights = travel days - 1.

5. Use the number of travellers provided by the user.

6. The budget assumptions are:

   Food: ₹800 per person per travel day
   Local transport: ₹300 per person per travel day
   Activities: ₹500 per person per sightseeing day

7. Food and local transport must be calculated
   using the total number of travel days.

8. Activities must be calculated only for sightseeing
   days. Do not count arrival and departure days
   as sightseeing days unless activities are scheduled.

9. Pass all these values to budget_estimation:
   - number_of_days
   - number_of_nights
   - number_of_travellers
   - activity_days

10. The hotel calculation assumes one room
    for the entire group.

11. Flight costs are multiplied by the number
    of travellers.

12. If no flight fare is available, clearly state
    that the total budget excludes flight expenses.

13. Never describe an unavailable flight fare
    as an estimated or confirmed price.

14. Explain that the budget is an estimate,
    not a confirmed booking price.

15. Display each budget component using the
    actual values returned by budget_estimation.
    Do not independently invent or recalculate
    budget figures in the final response.

--------------------------------------------------
H. OUTPUT FORMAT
--------------------------------------------------

Generate the travel plan using the following sections:

1. TRIP SUMMARY
   - Source city
   - Destination city
   - Travel dates
   - Duration
   - Number of travellers
   - Short trip overview

2. FLIGHT DETAILS
   - Available flight details, if any
   - Otherwise, explain flight unavailability
   - Return-flight availability

3. HOTEL RECOMMENDATION
   - Hotel name
   - Hotel ID
   - Star rating
   - Price per night
   - Amenities
   - Reason for selection

4. DAY-WISE ITINERARY
   - Day number and date
   - Arrival, sightseeing, or departure
   - Suggested attractions
   - Name, category, and rating
   - Free time where appropriate

5. WEATHER FORECAST
   - Date
   - Maximum temperature
   - Minimum temperature
   - Rain probability
   - Weather availability note, if needed

6. BUDGET BREAKDOWN
   - Hotel cost
   - Flight cost
   - Food cost
   - Activities cost
   - Local transport cost
   - Estimated total
   - Estimated cost per person

7. IMPORTANT NOTES
   - Dataset limitations
   - Flight-data limitations
   - Weather limitations, if any
   - Budget assumptions
   - Booking status

--------------------------------------------------
I. FINAL BEHAVIOUR
--------------------------------------------------

1. Be clear, organized, and professional.

2. Use only information supported by tool results.

3. Explain when data is unavailable.

4. Never claim that flights, hotels, or activities
   have been booked.

5. Do not hide limitations of the sample datasets.

6. Ensure that the itinerary, weather dates,
   hotel costs, and budget correspond to the
   same requested trip.
"""



# --------------------------------------------------
# 7. CREATE THE TRAVEL AGENT
# --------------------------------------------------

travel_agent = create_agent(
    model=llm,
    tools=travel_tools,
    system_prompt=SYSTEM_PROMPT
)


# --------------------------------------------------
# 8. STANDALONE TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("\nAI TRAVEL PLANNER")
    print("-" * 40)

    user_request = """
    Plan a 4-day trip from Bangalore to Goa.

    Travel start date: 2025-02-06
    Travel end date: 2025-02-09

    Number of travellers: 2

    Maximum hotel budget: ₹5000 per night.

    Please provide flight details, hotel recommendation,
    day-wise itinerary, weather availability, and budget.
    """


    print("\nGenerating travel plan...\n")

    try:

        response = travel_agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": user_request
                }
            ]
        })

        final_message = response["messages"][-1]
        content = final_message.content

        print("\n" + "=" * 60)
        print("GENERATED TRAVEL PLAN")
        print("=" * 60 + "\n")

        if isinstance(content, list):

            for item in content:

                if isinstance(item, dict) and "text" in item:
                    print(item["text"])

                elif isinstance(item, str):
                    print(item)

        else:
            print(content)

        print("\n" + "=" * 60)
        print("TRAVEL PLAN GENERATION COMPLETED")
        print("=" * 60)

    except Exception as error:

        print("\nAn error occurred while generating the travel plan:")
        print(error)
