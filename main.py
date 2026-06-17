from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from google import genai
import httpx
import os
import json

# file configurazione .env
load_dotenv()

app = FastAPI(
    title="Weather Wardrobe API",
    description="Motore di raccomandazione outfit basato su meteo e intelligenza artificiale"
)

# solo chiamate da localhost
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],  # solo richieste get
    allow_headers=["*"],
)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# caricamento API

# openWeather
if not WEATHER_API_KEY:
    raise RuntimeError("ERRORE DI CONFIGURAZIONE: WEATHER_API_KEY non trovata nel file .env!")

# genai
ai_client = None
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)

# modelli dati Pydantic
class DailyAdvice(BaseModel):
    date: str
    temperature: float
    condition: str
    main_condition: str
    is_raining: bool
    wind_speed: float
    outfit_advice: str

class WardrobeResponse(BaseModel):
    city: str
    forecasts: List[DailyAdvice]

# genera risposta con API gemini
async def generate_all_outfits_with_ai(weather_days: list) -> list:

    if not GEMINI_API_KEY or not ai_client:
        return ["Impossibile comunicare col server AI!"] * len(weather_days)

    try:
        # meteo per agent IA
        weather_summary = ""
        for idx, day in enumerate(weather_days):
            weather_summary += (
                f"- Giorno {idx + 1}: {day['temp']}°C, {day['condition']}, "
                f"Pioggia: {day['is_raining']}, Vento: {day['wind_speed']} km/h\n"
            )

        # prompt
        prompt = (
            f"Agisci come un maggiordomo che deve consigliare come vestirsi.\n"
            f"Ecco il meteo pianificato per i prossimi {len(weather_days)} giorni:\n"
            f"{weather_summary}\n"
            f"Genera un consiglio di abbigliamento (outfit) adatto a CIASCUN giorno.\n"
            f"Sii estremamente breve: massimo 25 parole per ciascun giorno.\n"
            f"Restituisci la risposta esclusivamente come un array JSON di stringhe, senza formattazione markdown "
            f"(evita di avvolgere il testo con i tag di blocco codice).\n"
            f"Esempio di formato di output richiesto: [\"Consiglio giorno 1\", \"Consiglio giorno 2\"]"
        )

        # chiamata asincrona
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        # pulizia stringa se c'è markdown inaspettato
        clean_text = response.text.strip()
        triple_backticks = "`" * 3

        # rimuovi intestazione json
        if clean_text.startswith(triple_backticks):
            clean_text = clean_text.replace(f"{triple_backticks}json", "")
            clean_text = clean_text.replace(f"{triple_backticks}", "")
            clean_text = clean_text.strip()

        # parse json in lista py
        outfit_list = json.loads(clean_text)
        return outfit_list

    except Exception as e:
        print(f"🔍 Errore interno Gemini API: {e}")
        return ["Errore nell'elaborazione della risposta!"] * len(weather_days)

# ENDPOINT
@app.get("/api/advise", response_model=WardrobeResponse)
async def get_wardrobe_advice(
        # sanifica output
        city: str = Query(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z\s\-]+$"),
        # valida giorni
        days: int = Query(default=1, ge=1, le=5)
):
    # intervalli da 3 ore OpenWeather
    cnt = days * 8
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=it&cnt={cnt}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Città non trovata. Controlla l'ortografia!")
        elif response.status_code != 200:
            raise HTTPException(status_code=500, detail="Errore nella comunicazione con il servizio meteo esterno.")

        data = response.json()

    city_name = data["city"]["name"]
    temporary_weather_list = []
    seen_dates = set()

    # parsa dati meteorologici
    for item in data["list"]:
        date_txt = item["dt_txt"]
        date_part = date_txt.split(" ")[0]
        time_part = date_txt.split(" ")[1]

        # condizioni di mezzogiorno
        if time_part == "12:00:00" or (date_part not in seen_dates and len(seen_dates) < days):
            if date_part in seen_dates:
                continue

            seen_dates.add(date_part)

            temp = item["main"]["temp"]
            condition = item["weather"][0]["description"].capitalize()
            weather_main = item["weather"][0]["main"].lower()

            is_raining = any(word in weather_main for word in ["rain", "drizzle", "storm"])
            wind_speed = round(item["wind"]["speed"] * 3.6, 1)  # m/s -> km/h

            temporary_weather_list.append({
                "date": date_part,
                "temp": temp,
                "condition": condition,
                "main_condition": weather_main,
                "is_raining": is_raining,
                "wind_speed": wind_speed
            })

    # chiamata BATCH singola
    ai_advices = await generate_all_outfits_with_ai(temporary_weather_list)

    # risultati
    extracted_forecasts = []
    for idx, w in enumerate(temporary_weather_list):
        advice_text = ai_advices[idx] if idx < len(ai_advices) else "Un look casual e comodo sarà perfetto!"

        extracted_forecasts.append(DailyAdvice(
            date=w["date"],
            temperature=w["temp"],
            condition=w["condition"],
            main_condition=w["main_condition"],
            is_raining=w["is_raining"],
            wind_speed=w["wind_speed"],
            outfit_advice=advice_text
        ))

    return WardrobeResponse(city=city_name, forecasts=extracted_forecasts)

# frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")