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

document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const cityInput = document.getElementById('cityInput').value;
    const daysSelect = document.getElementById('daysSelect').value;

    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('errorMessage');
    const resultsDiv = document.getElementById('results');
    const forecastGrid = document.getElementById('forecastGrid');
    const resultCity = document.getElementById('resultCity');

    errorDiv.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');

    try {
        const response = await fetch(`/api/advise?city=${encodeURIComponent(cityInput)}&days=${daysSelect}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Qualcosa è andato storto.');
        }

        const data = await response.json();

        resultCity.textContent = data.city;
        forecastGrid.innerHTML = '';

        if (data.forecasts.length > 1) {
            forecastGrid.className = "grid grid-cols-1 md:grid-cols-3 gap-4";
        } else {
            forecastGrid.className = "grid grid-cols-1 gap-4";
        }

        data.forecasts.forEach(day => {
            const dateObj = new Date(day.date);
            const formattedDate = dateObj.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' });
            const tempColor = day.temperature < 12 ? 'text-blue-400 bg-blue-950/50 border-blue-900/30' : day.temperature > 22 ? 'text-amber-400 bg-amber-950/50 border-amber-900/30' : 'text-emerald-400 bg-emerald-950/50 border-emerald-900/30';
            const weatherIcon = getWeatherIcon(day.main_condition);

            const card = document.createElement('div');
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
                </div>
            `;
            forecastGrid.appendChild(card);
        });

        resultsDiv.classList.remove('hidden');

    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.classList.remove('hidden');
    } finally {
        loadingDiv.classList.add('hidden');
    }
});