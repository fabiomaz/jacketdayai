function getWeatherIcon(mainCondition) {
    const icons = {
        'clear': '☀️',
        'clouds': '☁️',
        'rain': '🌧️',
        'drizzle': '🌦️',
        'thunderstorm': '⛈️',
        'snow': '❄️',
        'mist': '🌫️',
        'smoke': '🌫️',
        'haze': '🌫️',
        'dust': '🌫️',
        'fog': '🌫️',
        'sand': '🌫️',
        'ash': '🌫️',
        'squall': '💨',
        'tornado': '🌪️'
    };
    return icons[mainCondition] || '⛅';
}

// --- LOGICA GESTIONE DATE ---
const startDateInput = document.getElementById('startDate');
const endDateInput = document.getElementById('endDate');
const today = new Date();
const maxDate = new Date();
maxDate.setDate(today.getDate() + 4);

const minDateStr = formatDateISO(today);
const maxDateStr = formatDateISO(maxDate);

// limiti calendari
startDateInput.min = minDateStr;
startDateInput.max = maxDateStr;
startDateInput.value = minDateStr;

endDateInput.min = minDateStr;
endDateInput.max = maxDateStr;
endDateInput.value = minDateStr;

// controllo selezione date
startDateInput.addEventListener('change', () => {
    endDateInput.min = startDateInput.value;
    if (endDateInput.value < startDateInput.value) {
        endDateInput.value = startDateInput.value;
    }
});

// --- GESTIONE SUBMIT FORM ---
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const cityInput = document.getElementById('cityInput').value;
    const loadingDiv = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const errorDiv = document.getElementById('errorMessage');
    const resultsDiv = document.getElementById('results');
    const suitcaseGrid = document.getElementById('suitcaseGrid');
    const forecastGrid = document.getElementById('forecastGrid');
    const resultCity = document.getElementById('resultCity');

    errorDiv.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');

    // frasi di caricamento
    const funnyPhrases = [
        "Interrogando i satelliti...",
        "Consultando i fashion blogger più di tendenza...",
        "Sbirciando nell'armadio di Miranda Priestly...",
        "Calcolando l'impatto dell'umidità sui capelli...",
        "Abbinando i colori ai capricci del meteo...",
        "Stirando virtualmente le tue camicie..."
    ];
    let phraseIndex = 0;
    loadingText.textContent = funnyPhrases[0];

    const loadingInterval = setInterval(() => {
        phraseIndex = (phraseIndex + 1) % funnyPhrases.length;
        loadingText.style.opacity = 0;
        setTimeout(() => {
            loadingText.textContent = funnyPhrases[phraseIndex];
            loadingText.style.opacity = 1;
        }, 200);
    }, 2500);

    // calcolo indici giorni
    const startSelected = new Date(startDateInput.value);
    const endSelected = new Date(endDateInput.value);

    // normalizzazione date
    const todayMidnight = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const startMidnight = new Date(startSelected.getFullYear(), startSelected.getMonth(), startSelected.getDate());
    const endMidnight = new Date(endSelected.getFullYear(), endSelected.getMonth(), endSelected.getDate());

    const msPerDay = 24 * 60 * 60 * 1000;
    const startDayIndex = Math.round((startMidnight - todayMidnight) / msPerDay) + 1;
    const endDayIndex = Math.round((endMidnight - todayMidnight) / msPerDay) + 1;

    // indici finiti
    const daysRangeParam = `${startDayIndex}-${endDayIndex}`;

    try {
        // invio a API
        const response = await fetch(`/api/advise?city=${encodeURIComponent(cityInput)}&selected_days=${daysRangeParam}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Qualcosa è andato storto.');
        }

        const data = await response.json();

        resultCity.textContent = data.city;
        forecastGrid.innerHTML = '';
        suitcaseGrid.innerHTML = '';

        if (data.forecasts.length > 1) {
            forecastGrid.className = "grid grid-cols-1 md:grid-cols-3 gap-4";
        } else {
            forecastGrid.className = "grid grid-cols-1 gap-4";
        }

        suitcaseGrid.className = "grid grid-cols-1 gap-4";

        suitcaseGrid.innerHTML = `
    <div class="bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl flex flex-col justify-between transition-all hover:border-slate-700/50 hover:bg-slate-900/90 shadow-lg">
        <h3 class="text-cyan-400 font-bold mb-2">Cosa mettere in valigia:</h3>
        ${formatSuitcaseList(data.suitcase_advice)}
    </div>`;

        data.forecasts.forEach((day, index, array) => {

            const dateObj = new Date(day.date);
            const formattedDate = dateObj.toLocaleDateString('it-IT', {day: 'numeric', month: 'short'});
            const tempColor = day.temperature < 12 ? 'text-blue-400 bg-blue-950/50 border-blue-900/30' : day.temperature > 22 ? 'text-amber-400 bg-amber-950/50 border-amber-900/30' : 'text-emerald-400 bg-emerald-950/50 border-emerald-900/30';
            const weatherIcon = getWeatherIcon(day.main_condition);
            const card = document.createElement('div');

            const isLastIteration = index === array.length - 1;

            card.className = "bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl flex flex-col justify-between transition-all hover:border-slate-700/50 hover:bg-slate-900/90 shadow-lg";

            card.innerHTML = `
        <div>
            <div class="flex justify-between items-start mb-4">
                <div class="flex items-center gap-3">
                    <span class="text-3xl select-none filter drop-shadow-md">${weatherIcon}</span>
                    <div>
                        <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">${formattedDate}</p>
                        <h3 class="text-base font-bold text-slate-200 mt-0.5 leading-tight">${day.condition}</h3>
                    </div>
                </div>
                
                <div class="flex flex-col items-end gap-1">
                    <span class="text-sm font-bold px-2.5 py-0.5 rounded-xl border ${tempColor}">
                        ${Math.round(day.temperature)}°C
                    </span>
                    <span class="text-[10px] font-medium text-slate-400 bg-slate-950/40 px-1.5 py-0.5 rounded-md border border-slate-800/60 flex items-center gap-0.5">
                        💨 ${day.wind_speed} km/h
                    </span>
                </div>
            </div>
            
            ${day.is_raining ? `
                <div class="inline-flex items-center gap-1.5 text-[11px] text-cyan-400 bg-cyan-950/30 border border-cyan-900/40 px-2.5 py-0.5 rounded-full mb-3">
                    <span class="animate-pulse">💧</span> Bagnato
                </div>
            ` : ''}

            <p class="text-slate-300 text-sm leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-slate-850/60">
                <span class="text-cyan-400 font-medium">Consiglio:</span> ${day.outfit_advice}
            </p>

            ${isLastIteration ? `
                <div class="mt-3 text-xs text-purple-300 text-center font-bold">
                    ✨ Fine Previsioni ✨
                </div>
            ` : ''}
        </div>
    `;

            forecastGrid.appendChild(card);
        });

        resultsDiv.classList.remove('hidden');

    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.classList.remove('hidden');
    } finally {
        clearInterval(loadingInterval);
        loadingDiv.classList.add('hidden');
    }
});

// formatta data in YYYY-MM-DD
function formatDateISO(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// formatta lista "cosa mettere in valigia"

function formatSuitcaseList(text) {

    const items = text.split(/(?:•|\n\s*[\*-]\s)/)
        .map(item => item.trim())
        .filter(item => item.length > 0);

    // se l'ia non genera i punti crea paragrafo
    if (items.length === 1) {
        return `<p class="text-slate-300 text-sm leading-relaxed">${text}</p>`;
    }

    let html = '';
    let listStartIndex = 0;

    // isola frase precedente
    if (items[0].endsWith(':')) {
        html += `<p class="text-slate-300 text-sm font-semibold mb-3">${items[0]}</p>`;
        listStartIndex = 1;
    }

    // genera elementi
    const listItems = items.slice(listStartIndex).map(item => `<li>${item}</li>`).join('');
    html += `<ul class="list-disc list-outside ml-5 text-slate-300 text-sm leading-relaxed space-y-1.5 marker:text-cyan-500">${listItems}</ul>`;

    return html;
}
