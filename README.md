# JacketDayAI

**JacketDayAI** è una web application full-stack asincrona sviluppata in **Python (FastAPI)** 
Mai piu dubbi su cosa mettere in valigia!
JacketDay è il tuo maggiordomo virtuale che analizza le previsioni meteo in tempo reale e sfrutta l'intelligenza artificiale per consigliarti l'outfit perfetto per i prossimi giorni.

---

## Caratteristiche principali

* **Architettura Asincrona:** Sviluppata interamente con **FastAPI** e **HTTPX** per gestire le richieste.
* **AI-Powered Stylist:** Integrazione con l'SDK ufficiale di **Google GenAI** utilizzando il modello `gemini-2.5-flash`.
* **Smart Batching (Ottimizzazione Quota):** l'applicazione raggruppa i dati meteo ed esegue **una sola chiamata cumulativa**, richiedendo un output in formato JSON strutturato.
* **UI:** Frontend minimale sviluppato in **HTML5** e **Tailwind CSS**, servito direttamente da FastAPI tramite il modulo `StaticFiles`.

---

## Tech Stack

| Componente | Tecnologie Utilizzate |
| :--- | :--- |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, HTTPX |
| **Intelligenza Artificiale** | Google GenAI SDK (`gemini-2.5-flash`) |
| **Frontend** | HTML5, JavaScript (Fetch API), Tailwind CSS |
| **Sicurezza & Config** | Pydantic (Validazione dati), Python-dotenv, CORS Middleware |
| **API Esterne** | OpenWeatherMap API (5 Day / 3 Hour Forecast) |

---

## Installazione e Configurazione

### 1. Clonazione del Repository
```bash
git clone [https://github.com/fabiomaz/jacketdayai.git](https://github.com/fabiomaz/jacketdayai.git)
cd weather-wardrobe 
```
### 2. Creazione dell'Ambiente Virtuale

# Su Windows
```bash
python -m venv .venv
.venv\Scripts\activate
```
# Su macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```
### 3. Installazione delle Dipendenze
```bash
pip install -r requirements.txt
```

### 4. Configurazione delle Variabili d'Ambiente
```bash
WEATHER_API_KEY=il_tuo_token_openweathermap
GEMINI_API_KEY=la_tua_chiave_api_gemini
```

### 5. Avvio del Server

```bash
uvicorn main:app --reload
```

L'applicazione sarà raggiungibile nel tuo browser all'indirizzo: http://127.0.0.1:8000
