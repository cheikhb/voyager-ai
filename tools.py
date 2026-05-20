"""
tools.py  –  LangChain tools for the Travel Agent

Real tools (require SerpAPI key):
  - FlightSearchTool   → searches Google Flights via SerpAPI
  - HotelSearchTool    → searches Google Hotels via SerpAPI

Simulated tools (always available – realistic demo data):
  - ActivitySearchTool
  - ItineraryBuilderTool
  - BookingTool
  - WeatherTool
  - CurrencyConverterTool
  - TravelAdvisoryTool
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from typing import ClassVar, Dict, Optional, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════════════
# Input schemas
# ══════════════════════════════════════════════════════════════════════════════

class FlightSearchInput(BaseModel):
    origin: str = Field(description="Origin city or airport code")
    destination: str = Field(description="Destination city or airport code")
    departure_date: str = Field(description="Departure date YYYY-MM-DD")
    return_date: Optional[str] = Field(default=None, description="Return date YYYY-MM-DD for round-trip")
    passengers: int = Field(default=1, description="Number of passengers")
    cabin_class: str = Field(default="economy", description="economy | business | first")

class HotelSearchInput(BaseModel):
    destination: str = Field(description="City or area to search hotels in")
    check_in: str = Field(description="Check-in date YYYY-MM-DD")
    check_out: str = Field(description="Check-out date YYYY-MM-DD")
    guests: int = Field(default=2)
    budget_per_night: Optional[str] = Field(default=None, description="e.g. $100-$300")

class ActivitySearchInput(BaseModel):
    destination: str = Field(description="City or region")
    interests: str = Field(description="Comma-separated interests, e.g. 'culture,food,adventure'")
    duration_days: int = Field(default=3, description="Number of days to fill")

class ItineraryInput(BaseModel):
    destination: str
    duration_days: int
    travel_style: str = Field(description="e.g. 'cultural, relaxed, adventure'")
    budget: str = Field(description="e.g. 'mid-range $2000'")
    group_type: str = Field(default="couple")

class BookingInput(BaseModel):
    item_type: str = Field(description="flight | hotel | activity")
    item_id: str = Field(description="ID from search results")
    passenger_name: str
    email: str
    special_requests: Optional[str] = None

class WeatherInput(BaseModel):
    destination: str
    travel_date: str = Field(description="YYYY-MM-DD")

class CurrencyInput(BaseModel):
    amount: float
    from_currency: str = Field(description="e.g. USD, EUR, GBP")
    to_currency: str = Field(description="e.g. JPY, THB, AUD")

class AdvisoryInput(BaseModel):
    destination: str
    nationality: str = Field(default="US", description="Traveller's nationality for visa info")


# ══════════════════════════════════════════════════════════════════════════════
# Tool implementations
# ══════════════════════════════════════════════════════════════════════════════

class FlightSearchTool(BaseTool):
    name: str = "search_flights"
    description: str = (
        "Search for available flights between two cities. "
        "Returns a list of flight options with prices, airlines, and schedules."
    )
    args_schema: Type[BaseModel] = FlightSearchInput
    serpapi_key: Optional[str] = None

    def _run(self, origin: str, destination: str, departure_date: str,
             return_date: str = None, passengers: int = 1, cabin_class: str = "economy") -> str:

        if self.serpapi_key:
            return self._live_search(origin, destination, departure_date, return_date, passengers, cabin_class)
        return self._simulated(origin, destination, departure_date, return_date, passengers, cabin_class)

    def _live_search(self, origin, destination, departure_date, return_date, passengers, cabin_class) -> str:
        try:
            from serpapi import GoogleSearch
            params = {
                "engine": "google_flights",
                "departure_id": origin.upper(),
                "arrival_id": destination.upper(),
                "outbound_date": departure_date,
                "currency": "USD",
                "hl": "en",
                "api_key": self.serpapi_key,
            }
            if return_date:
                params["return_date"] = return_date
            results = GoogleSearch(params).get_dict()
            flights = results.get("best_flights", [])[:3]
            if not flights:
                flights = results.get("other_flights", [])[:3]
            return json.dumps({"source": "live", "flights": flights}, indent=2)
        except Exception as e:
            return self._simulated(origin, destination, departure_date, return_date, passengers, cabin_class)

    def _simulated(self, origin, destination, departure_date, return_date, passengers, cabin_class) -> str:
        airlines = ["Air France", "Lufthansa", "Emirates", "Singapore Airlines", "Qatar Airways", "British Airways"]
        multiplier = {"economy": 1, "business": 4, "first": 8}.get(cabin_class, 1)
        flights = []
        for i in range(3):
            base = random.randint(350, 900)
            price = base * multiplier * passengers
            dep_h = random.randint(6, 20)
            dur_h = random.randint(2, 14)
            flights.append({
                "id": f"FL{1000+i}",
                "airline": random.choice(airlines),
                "flight_number": f"{random.choice(['AF','LH','EK','SQ','QR','BA'])}{random.randint(100,999)}",
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure": f"{departure_date} {dep_h:02d}:00",
                "arrival": f"{departure_date} {(dep_h+dur_h)%24:02d}:30",
                "duration": f"{dur_h}h 30m",
                "stops": random.choice([0, 0, 1]),
                "cabin": cabin_class,
                "price_usd": price,
                "luggage": "23kg included" if cabin_class != "economy" else "Cabin bag only",
                "refundable": i == 0,
            })
        return json.dumps({"source": "simulated", "flights": flights}, indent=2)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class HotelSearchTool(BaseTool):
    name: str = "search_hotels"
    description: str = (
        "Search for hotels or accommodations in a destination. "
        "Returns options with ratings, amenities, and prices per night."
    )
    args_schema: Type[BaseModel] = HotelSearchInput
    serpapi_key: Optional[str] = None

    def _run(self, destination: str, check_in: str, check_out: str,
             guests: int = 2, budget_per_night: str = None) -> str:

        if self.serpapi_key:
            return self._live_search(destination, check_in, check_out, guests)
        return self._simulated(destination, check_in, check_out, guests, budget_per_night)

    def _live_search(self, destination, check_in, check_out, guests) -> str:
        try:
            from serpapi import GoogleSearch
            params = {
                "engine": "google_hotels",
                "q": f"hotels in {destination}",
                "check_in_date": check_in,
                "check_out_date": check_out,
                "adults": guests,
                "currency": "USD",
                "hl": "en",
                "api_key": self.serpapi_key,
            }
            results = GoogleSearch(params).get_dict()
            hotels = results.get("properties", [])[:4]
            return json.dumps({"source": "live", "hotels": hotels}, indent=2)
        except Exception as e:
            return self._simulated(destination, check_in, check_out, guests, None)

    def _simulated(self, destination, check_in, check_out, guests, budget) -> str:
        styles = [
            {"name": f"Grand {destination} Palace", "stars": 5, "base": 280, "amenities": ["Spa", "Pool", "Gym", "Fine Dining", "Concierge"]},
            {"name": f"{destination} Boutique Suites", "stars": 4, "base": 150, "amenities": ["Pool", "Breakfast", "Bar", "Rooftop"]},
            {"name": f"The {destination} Central", "stars": 4, "base": 120, "amenities": ["Gym", "Restaurant", "Business Centre"]},
            {"name": f"Cosy Nest {destination}", "stars": 3, "base": 75, "amenities": ["Free WiFi", "Breakfast", "Parking"]},
        ]
        try:
            nights = (datetime.strptime(check_out, "%Y-%m-%d") - datetime.strptime(check_in, "%Y-%m-%d")).days
        except:
            nights = 1

        hotels = []
        for h in styles:
            price_pn = h["base"] + random.randint(-20, 30)
            hotels.append({
                "id": f"HTL{random.randint(1000,9999)}",
                "name": h["name"],
                "stars": h["stars"],
                "rating": round(random.uniform(7.8, 9.7), 1),
                "reviews": random.randint(200, 3500),
                "location": f"City Centre, {destination}",
                "price_per_night_usd": price_pn,
                "total_usd": price_pn * nights,
                "nights": nights,
                "amenities": h["amenities"],
                "free_cancellation": random.choice([True, True, False]),
                "breakfast_included": h["stars"] >= 4,
            })
        return json.dumps({"source": "simulated", "hotels": hotels}, indent=2)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class ActivitySearchTool(BaseTool):
    name: str = "search_activities"
    description: str = (
        "Search for things to do, tours, and experiences at a destination. "
        "Returns curated activities with descriptions, prices, and duration."
    )
    args_schema: Type[BaseModel] = ActivitySearchInput

    def _run(self, destination: str, interests: str, duration_days: int = 3) -> str:
        interest_list = [i.strip().lower() for i in interests.split(",")]

        activity_db = {
            "culture": [
                {"name": "Old Town Walking Tour", "duration": "3h", "price": 25, "type": "Culture"},
                {"name": "Local Museum Skip-the-Line", "duration": "2h", "price": 18, "type": "Culture"},
                {"name": "Traditional Cooking Class", "duration": "4h", "price": 65, "type": "Culture & Food"},
                {"name": "Historic Landmarks Private Tour", "duration": "6h", "price": 120, "type": "Culture"},
            ],
            "food": [
                {"name": "Street Food Night Market Tour", "duration": "3h", "price": 45, "type": "Gastronomy"},
                {"name": "Wine & Cheese Tasting", "duration": "2h", "price": 55, "type": "Gastronomy"},
                {"name": "Farm-to-Table Cooking Experience", "duration": "5h", "price": 90, "type": "Gastronomy"},
                {"name": "Michelin Restaurant Tasting Menu", "duration": "3h", "price": 180, "type": "Fine Dining"},
            ],
            "adventure": [
                {"name": "Sunrise Hike with Guide", "duration": "5h", "price": 60, "type": "Adventure"},
                {"name": "Kayaking & Snorkelling", "duration": "4h", "price": 75, "type": "Water Sports"},
                {"name": "Zip-lining Experience", "duration": "3h", "price": 55, "type": "Adventure"},
                {"name": "Rock Climbing for Beginners", "duration": "4h", "price": 80, "type": "Adventure"},
            ],
            "nature": [
                {"name": "National Park Day Trip", "duration": "8h", "price": 85, "type": "Nature"},
                {"name": "Botanical Garden & Wildlife Tour", "duration": "3h", "price": 35, "type": "Nature"},
                {"name": "Sunset Boat Cruise", "duration": "2h", "price": 50, "type": "Nature"},
            ],
            "wellness": [
                {"name": "Sunrise Yoga on the Beach", "duration": "1.5h", "price": 20, "type": "Wellness"},
                {"name": "Traditional Spa & Massage", "duration": "2h", "price": 70, "type": "Wellness"},
                {"name": "Meditation Retreat Day", "duration": "6h", "price": 95, "type": "Wellness"},
            ],
        }

        selected = []
        for interest in interest_list:
            for key in activity_db:
                if interest in key or key in interest:
                    selected.extend(activity_db[key])

        if not selected:
            for acts in activity_db.values():
                selected.extend(acts[:1])

        # Deduplicate and enrich
        seen, final = set(), []
        for act in selected:
            if act["name"] not in seen:
                seen.add(act["name"])
                final.append({
                    **act,
                    "id": f"ACT{random.randint(1000,9999)}",
                    "destination": destination,
                    "rating": round(random.uniform(4.2, 5.0), 1),
                    "reviews": random.randint(50, 1200),
                    "group_size": f"Up to {random.choice([8,12,15,20])} people",
                    "languages": ["English", random.choice(["French", "Spanish", "German", "Japanese"])],
                    "booking_required": random.choice([True, True, False]),
                })

        return json.dumps({
            "destination": destination,
            "activities_found": len(final),
            "activities": final[:min(8, duration_days * 3)],
        }, indent=2)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class ItineraryBuilderTool(BaseTool):
    name: str = "build_itinerary"
    description: str = (
        "Create a detailed day-by-day itinerary for a trip. "
        "Combines flights, hotels, and activities into a coherent travel plan with timing."
    )
    args_schema: Type[BaseModel] = ItineraryInput

    def _run(self, destination: str, duration_days: int, travel_style: str,
             budget: str, group_type: str = "couple") -> str:
        days = []
        for d in range(1, duration_days + 1):
            if d == 1:
                day = {
                    "day": d,
                    "title": f"Arrival in {destination}",
                    "morning": "Arrive at airport, transfer to hotel, check-in",
                    "afternoon": f"Leisurely explore the neighbourhood around your hotel in {destination}",
                    "evening": f"Welcome dinner at a local {destination} restaurant – try the signature dish",
                    "tips": "Keep the first day light to recover from travel. Exchange some currency at the airport.",
                    "estimated_spend": "$50–$120",
                }
            elif d == duration_days:
                day = {
                    "day": d,
                    "title": "Farewell Day & Departure",
                    "morning": "Last breakfast, final souvenir shopping",
                    "afternoon": "Check-out, transfer to airport",
                    "evening": "Departure flight",
                    "tips": "Leave extra time for check-in. Keep receipts for duty-free refunds.",
                    "estimated_spend": "$30–$80",
                }
            else:
                themes = [
                    ("Historic Heart", "Visit the old town and main landmarks", "Local market lunch", "Rooftop bar sunset"),
                    ("Cultural Immersion", "Museum morning with audio guide", "Traditional restaurant", "Cultural show or live music"),
                    ("Day Trip", "Excursion to nearby attraction", "Picnic or local eatery", "Relaxed evening in"),
                    ("Food & Markets", "Cooking class or food tour", "Street food exploration", "Fine dining experience"),
                    ("Nature & Outdoors", "Hiking trail or nature walk", "Al fresco lunch", "Spa evening"),
                ]
                theme = themes[(d - 2) % len(themes)]
                day = {
                    "day": d,
                    "title": theme[0],
                    "morning": theme[1],
                    "afternoon": theme[2],
                    "evening": theme[3],
                    "tips": f"Book ahead for popular spots. Comfortable shoes recommended.",
                    "estimated_spend": "$80–$180",
                }
            days.append(day)

        return json.dumps({
            "destination": destination,
            "duration_days": duration_days,
            "travel_style": travel_style,
            "budget": budget,
            "group_type": group_type,
            "itinerary": days,
            "packing_essentials": ["Universal adapter", "Travel insurance docs", "Comfortable walking shoes",
                                   "Light layers", "Reusable water bottle", "Offline maps downloaded"],
            "money_saving_tips": [
                "Book accommodation 6–8 weeks ahead for best rates",
                "Use public transport for daytime sightseeing",
                "Lunch at local spots is often half the price of dinner",
                "City tourist cards often pay for themselves in 2 days",
            ],
        }, indent=2)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class BookingTool(BaseTool):
    name: str = "make_booking"
    description: str = (
        "Book a flight, hotel, or activity. Returns a booking confirmation with reference number."
    )
    args_schema: Type[BaseModel] = BookingInput

    def _run(self, item_type: str, item_id: str, passenger_name: str,
             email: str, special_requests: str = None) -> str:
        ref = f"VOY-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000,99999)}"
        return json.dumps({
            "status": "CONFIRMED",
            "booking_reference": ref,
            "item_type": item_type,
            "item_id": item_id,
            "passenger_name": passenger_name,
            "email": email,
            "special_requests": special_requests or "None",
            "confirmation_sent_to": email,
            "cancellation_deadline": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "support_line": "+1-800-VOYAGER",
            "message": f"Your {item_type} has been successfully booked! Reference: {ref}",
        }, indent=2)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class WeatherTool(BaseTool):
    name: str = "get_weather_forecast"
    description: str = (
        "Get weather forecast and best time to visit information for a destination."
    )
    args_schema: Type[BaseModel] = WeatherInput

    def _run(self, destination: str, travel_date: str) -> str:
        conditions = ["Sunny ☀️", "Partly Cloudy 🌤️", "Warm & Humid 🌡️", "Mild & Breezy 🌬️", "Occasional Showers 🌦️"]
        temp_c = random.randint(18, 30)
        return json.dumps({
            "destination": destination,
            "travel_date": travel_date,
            "forecast": random.choice(conditions),
            "temperature_c": temp_c,
            "temperature_f": round(temp_c * 9/5 + 32),
            "humidity_pct": random.randint(40, 80),
            "rainfall_chance_pct": random.randint(5, 40),
            "uv_index": random.randint(3, 9),
            "sea_temp_c": temp_c - random.randint(2, 5),
            "clothing_advice": "Light clothing recommended. Pack a light layer for evenings.",
            "best_months_to_visit": ["March–May", "September–November"],
            "avoid": "August (peak crowds), January (rainy season)",
        }, indent=2)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class CurrencyConverterTool(BaseTool):
    name: str = "convert_currency"
    description: str = "Convert amounts between currencies with approximate exchange rates."
    args_schema: Type[BaseModel] = CurrencyInput

    RATES: ClassVar[Dict[str, float]] = {  # Approximate rates vs USD
        "USD": 1.0, "EUR": 0.93, "GBP": 0.79, "JPY": 149.5, "AUD": 1.52,
        "CAD": 1.36, "CHF": 0.89, "CNY": 7.24, "INR": 83.1, "THB": 35.2,
        "SGD": 1.34, "AED": 3.67, "MXN": 17.2, "BRL": 4.97, "KRW": 1325,
    }

    def _run(self, amount: float, from_currency: str, to_currency: str) -> str:
        fc, tc = from_currency.upper(), to_currency.upper()
        rate_from = self.RATES.get(fc, 1.0)
        rate_to = self.RATES.get(tc, 1.0)
        usd_amount = amount / rate_from
        converted = usd_amount * rate_to
        return json.dumps({
            "from": f"{amount:,.2f} {fc}",
            "to": f"{converted:,.2f} {tc}",
            "exchange_rate": round(rate_to / rate_from, 4),
            "note": "Indicative rate only. Check your bank/card for actual rates.",
        }, indent=2)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class TravelAdvisoryTool(BaseTool):
    name: str = "get_travel_advisory"
    description: str = (
        "Get visa requirements, travel advisories, health requirements, "
        "and essential entry information for a destination."
    )
    args_schema: Type[BaseModel] = AdvisoryInput

    def _run(self, destination: str, nationality: str = "US") -> str:
        return json.dumps({
            "destination": destination,
            "traveller_nationality": nationality,
            "visa_required": random.choice([True, False]),
            "visa_on_arrival": random.choice([True, False]),
            "evisa_available": True,
            "passport_validity_required": "6 months beyond travel dates",
            "travel_advisory_level": random.choice(["Level 1 – Normal Precautions", "Level 1 – Normal Precautions", "Level 2 – Exercise Increased Caution"]),
            "health_requirements": {
                "vaccinations_recommended": random.sample(["Hepatitis A", "Typhoid", "Yellow Fever", "Rabies"], 2),
                "covid_requirements": "No restrictions currently",
                "travel_insurance": "Strongly recommended",
            },
            "customs_rules": {
                "currency_limit": "$10,000 USD without declaration",
                "prohibited": ["Certain foods", "Drones without permit"],
            },
            "emergency_contacts": {
                "police": "112",
                "ambulance": "112",
                "us_embassy": "+1-202-501-4444",
            },
            "note": "Always verify with official government sources before travelling.",
        }, indent=2)

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


# ══════════════════════════════════════════════════════════════════════════════
# Factory
# ══════════════════════════════════════════════════════════════════════════════

def build_tools(serpapi_key: str | None = None) -> list:
    return [
        FlightSearchTool(serpapi_key=serpapi_key),
        HotelSearchTool(serpapi_key=serpapi_key),
        ActivitySearchTool(),
        ItineraryBuilderTool(),
        BookingTool(),
        WeatherTool(),
        CurrencyConverterTool(),
        TravelAdvisoryTool(),
    ]