from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from google import genai
import httpx
import os
import json

from starlette.staticfiles import StaticFiles

# carica configurazione se presente in locale
load_dotenv()

app = FastAPI(
    title="Weather Wardrobe API",
    description="Motore di raccomandazione outfit basato su meteo e intelligenza artificiale"
)

# controllo richieste
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],  # Solo richieste GET
    allow_headers=["*"],
)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# verifica configurazione
if not WEATHER_API_KEY:
    raise RuntimeError("ERRORE DI CONFIGURAZIONE: WEATHER_API_KEY non trovata nelle variabili d'ambiente!")

if not GEMINI_API_KEY:
    raise RuntimeError("ERRORE DI CONFIGURAZIONE: GEMINI_API_KEY non trovata nelle variabili d'ambiente!")

# genai
ai_client = genai.Client(api_key=GEMINI_API_KEY)


# Modelli dati
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
    suitcase_advice: str


# risposta API Gemini
async def generate_all_outfits_with_ai(weather_days: list) -> list:
    try:

        # meteo per prompt
        weather_summary = ""
        for idx, day in enumerate(weather_days):
            weather_summary += (
                f"- Giorno {idx + 1}: {day['temp']}°C, {day['condition']}, "
                f"Pioggia: {day['is_raining']}, Vento: {day['wind_speed']} km/h\n"
            )

        # prompt
        prompt = (
            f"Fornisci un consiglio lucido e intelligente su come vestirmi.\n"
            f"Ecco il meteo pianificato per i prossimi {len(weather_days)} giorni:\n"
            f"{weather_summary}\n"
            f"Genera un consiglio di abbigliamento (outfit) adatto a CIASCUN giorno, incrociando i dati con le medie"
            f"stagionali del periodo in modo da dare un consiglio utile anche in caso di eventuali cambiamenti repentini del tempo.\n"
            f"Sii estremamente breve: massimo 45 parole per ciascun giorno.\n"
            f"Aggiungi poi un ultimo consiglio (senza limiti di parole), cioè cosa mettere in valigia per un viaggio nella località scelta e per questi giorni \n"
            f"(sottoforma di lista con elenco puntato), comprensivo di biancheria e accessori vari (toilette, ciabatte ecc). In questo consiglio includi anche \n"
            f"cose extra che potrebbero servire nella destinazione (ad esempio delle precauzioni per i midges se si visita la Scozia).\n"
            f"Restituisci la risposta esclusivamente come un array JSON di stringhe (tante posizioni quanti sono i giorni + una di consiglio valigia), senza formattazione markdown "
            f"(evita di avvolgere il testo con i tag di blocco codice).\n"
            f"Esempio di formato di output richiesto: [\"Consiglio giorno 1\", \"Consiglio giorno 2\"]"
        )

        # chiamata asincrona
        chat = ai_client.aio.chats.create(model='gemini-2.5-flash')
        response = await chat.send_message(message=prompt)

        # pulizia markdown eventuale
        clean_text = response.text.strip()
        triple_backticks = "`" * 3

        if clean_text.startswith(triple_backticks):
            clean_text = clean_text.replace(f"{triple_backticks}json", "")
            clean_text = clean_text.replace(f"{triple_backticks}", "")
            clean_text = clean_text.strip()

        # parsa json
        outfit_list = json.loads(clean_text)

        return outfit_list

    except Exception as e:
        print(f"🔍 Errore interno Gemini API: {e}")
        return ["Errore nell'elaborazione della risposta da parte dell'IA."] * len(weather_days)


# ENDPOINT API
@app.get("/api/advise", response_model=WardrobeResponse)
async def get_wardrobe_advice(
        city: str = Query(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z\s\-]+$"),
        selected_days: str = Query(max_length=10, pattern=r"^\d+-\d+$"),
):
    # giorni desiderati
    try:
        start_day, end_day = [int(num) for num in selected_days.split("-")]
        if start_day > end_day or start_day < 1:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato giorni non valido.")

    # API Openweather (3 ore)
    days = 5  # limite giorni free
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

    # una sola previsione per giorno
    daily_weather_dict = {}

    for item in data["list"]:
        date_txt = item["dt_txt"]
        date_part, time_part = date_txt.split(" ")

        # primo orario disponibile
        if date_part not in daily_weather_dict:
            daily_weather_dict[date_part] = item
        # se no ore 12:00
        elif time_part == "12:00:00":
            daily_weather_dict[date_part] = item

        if len(daily_weather_dict) == days and time_part == "12:00:00":
            break

    # lista ordinata cronologicamente
    all_days_list = list(daily_weather_dict.values())
    filtered_days = all_days_list[(start_day - 1):end_day]

    # lista pulita
    temporary_weather_list = []

    for item in filtered_days:
        date_part = item["dt_txt"].split(" ")[0]
        temp = item["main"]["temp"]
        condition = item["weather"][0]["description"].capitalize()
        weather_main = item["weather"][0]["main"].lower()
        is_raining = any(word in weather_main for word in ["rain", "drizzle", "storm"])
        wind_speed = round(item["wind"]["speed"] * 3.6, 1)

        temporary_weather_list.append({
            "date": date_part,
            "temp": temp,
            "condition": condition,
            "main_condition": weather_main,
            "is_raining": is_raining,
            "wind_speed": wind_speed
        })

    # chiamata singola a gemini
    ai_advices = await generate_all_outfits_with_ai(temporary_weather_list)

    # consiglio valigia
    suitcase_text = ai_advices.pop() if len(ai_advices) > len(
        temporary_weather_list) else "Nessun consiglio valigia disponibile."

    # risposta validata da Pydantic
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

    return WardrobeResponse(
        city=city_name,
        forecasts=extracted_forecasts,
        suitcase_advice=suitcase_text
    )

# frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")

def trova_modelli_gemini():
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    client = genai.Client(api_key=GEMINI_API_KEY)

    print("Modelli disponibili per la generazione di testo:")
    for model in client.models.list():
        print(model.name)
