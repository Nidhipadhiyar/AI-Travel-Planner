# ✈️ AI Travel Planning Assistant

An Agentic AI-powered travel planning application that creates personalized, budget-aware travel itineraries using **LangChain, Google Gemini, Python, and Streamlit**.

The application helps users plan trips by searching available flights, recommending hotels, discovering tourist attractions, checking weather forecasts, and estimating travel expenses.

## 🌍 Project Overview

Planning a trip involves comparing transportation, accommodation, attractions, weather conditions, and expenses.

This project uses an AI agent that understands user requirements, selects relevant tools, retrieves information, and generates a structured travel plan.

## ✨ Key Features

- **Flight Search:** Search available flights using the provided flight dataset.
- **Hotel Recommendations:** Find hotels based on destination and nightly budget.
- **Tourist Attractions:** Discover available places and attractions.
- **Weather Forecast:** Retrieve weather information using the Open-Meteo API.
- **Smart Budget Estimation:** Calculate flight, accommodation, food, transportation, and activity costs.
- **AI-Powered Itinerary:** Generate personalized day-wise travel plans.
- **PDF Export:** Download the generated travel plan as a PDF.
- **Structured Output:** Present trip details, recommendations, weather, and budget breakdown.

## 🧠 Agent Workflow

The application uses a LangChain agent powered by Google Gemini.

1. The user enters travel details through the Streamlit interface.
2. The AI agent understands the travel requirements.
3. The agent selects and invokes relevant tools.
4. Tools retrieve information from JSON datasets and the weather API.
5. The budget tool estimates the overall trip expenses.
6. The agent combines the results into a structured itinerary.
7. The user views the travel plan and can download it as a PDF.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Agent Framework | LangChain |
| Large Language Model | Google Gemini |
| Frontend | Streamlit |
| Weather API | Open-Meteo |
| Data Storage | JSON datasets |
| PDF Generation | ReportLab |
| Environment Variables | python-dotenv |

## 📁 Project Structure

```text
AI-Travel-Planner/
│
├── agents/
│   └── travel_agent.py
│
├── tools/
│   ├── travel_tools.py
│   ├── weather_tool.py
│   └── budget_tool.py
│
├── data/
│   ├── flights.json
│   ├── hotels.json
│   └── places.json
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

*The structure above should be adjusted to match the final files uploaded to the repository.*

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or a compatible version for the installed dependencies
- Git
- Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/Nidhipadhiyar/AI-Travel-Planner.git
cd AI-Travel-Planner
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_gemini_api_key
```

Replace the placeholder with your own API key.

**Important:** Never upload your `.env` file or expose your API key publicly.

### 5. Run the application

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

## 🌦️ External API

This project uses the **Open-Meteo API** to retrieve weather forecasts.

- No API key is required for the weather API used in this project.
- Weather availability depends on the forecast window supported by the service.

## 📊 Dataset Information

The project uses three JSON datasets:

- `flights.json` – flight details, routes, timings, airlines, and prices.
- `hotels.json` – hotel names, locations, star ratings, prices, and amenities.
- `places.json` – attraction names, cities, categories, and ratings.

**Dataset limitation:** The datasets contain sample records. Flight dates are historical, and the listed options may not represent currently available commercial services. Hotel and attraction records should also be treated as sample data rather than verified live listings.

## 💰 Budget Estimation

The budget estimator calculates:

- Flight expenses
- Hotel accommodation
- Food expenses
- Local transportation
- Activities and sightseeing

The final estimate depends on the number of travellers, days, nights, and selected options. It is an estimated budget, not a confirmed booking price.

## ⚠️ Limitations

- Flight, hotel, and attraction information comes from the supplied sample datasets.
- Weather forecasts are limited by Open-Meteo forecast availability.
- The application does not book flights or hotels.
- Budget estimates are based on predefined assumptions and sample prices.

## 🚀 Future Improvements

- Integration with live flight and hotel APIs.
- Real-time booking availability.
- Interactive maps and route optimization.
- More destination datasets.
- Advanced travel preference filtering.

## 👩‍💻 Author

**Nidhi Padhiyar**

GitHub: [Nidhipadhiyar](https://github.com/Nidhipadhiyar)

---

*Developed as an Agentic AI project using LangChain and Google Gemini.*