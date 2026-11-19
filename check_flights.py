import pandas as pd

flights = pd.read_json("data/flights.json")

results = flights[
    (flights["from"].str.lower() == "bangalore") &
    (flights["to"].str.lower() == "goa")
]

print("\nBANGALORE TO GOA FLIGHTS")
print("-" * 40)

if results.empty:
    print("No flights found for this route.")
else:
    print(results.to_string(index=False))