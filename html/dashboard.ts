// Energy Dashboard - client-side rendering
// Fetches JSON data and renders ComEd pricing, Ecobee thermostat, and solar panels.

// ===========================================================
// Color utilities (ported from energylib/htmltools.py)
// ===========================================================

// Linear interpolation between breakpoints
function interpolate(x: number, xPoints: number[], yPoints: number[]): number {
	if (x <= xPoints[0]) return yPoints[0];
	if (x >= xPoints[xPoints.length - 1]) return yPoints[yPoints.length - 1];
	for (let i = 0; i < xPoints.length - 1; i++) {
		if (x >= xPoints[i] && x <= xPoints[i + 1]) {
			const t = (x - xPoints[i]) / (xPoints[i + 1] - xPoints[i]);
			return yPoints[i] + t * (yPoints[i + 1] - yPoints[i]);
		}
	}
	return yPoints[yPoints.length - 1];
}

// HSV to RGB (h in 0-1, s in 0-1, v in 0-1)
function hsvToRgb(h: number, s: number, v: number): [number, number, number] {
	let r = 0, g = 0, b = 0;
	const i = Math.floor(h * 6);
	const f = h * 6 - i;
	const p = v * (1 - s);
	const q = v * (1 - f * s);
	const t = v * (1 - (1 - f) * s);
	switch (i % 6) {
		case 0: r = v; g = t; b = p; break;
		case 1: r = q; g = v; b = p; break;
		case 2: r = p; g = v; b = t; break;
		case 3: r = p; g = q; b = v; break;
		case 4: r = t; g = p; b = v; break;
		case 5: r = v; g = p; b = q; break;
	}
	return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

// Detect dark mode
function isDarkMode(): boolean {
	return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

// Price to color string (matches htmltools.py colorPrice)
function priceColor(price: number): string {
	const xPrice = [-100, 0, 3, 5, 7, 9, 11, 100];
	const yHue = [315, 240, 180, 120, 60, 15, 5, 0];
	const hue = interpolate(price, xPrice, yHue);
	// In dark mode, bump value for readability
	const val = isDarkMode() ? 0.85 : 0.6;
	const sat = 0.9;
	const [r, g, b] = hsvToRgb(hue / 360, sat, val);
	return `rgb(${r}, ${g}, ${b})`;
}

// Temperature to color string (matches htmltools.py colorTemperature)
function tempColor(temp: number): string {
	const xTemp = [-100, 0, 50, 60, 65, 70, 76, 85, 100, 250];
	const yHue = [330, 270, 240, 210, 180, 170, 90, 30, 10, 0];
	const hue = interpolate(temp, xTemp, yHue);
	const val = isDarkMode() ? 0.85 : 0.6;
	const sat = 0.9;
	const [r, g, b] = hsvToRgb(hue / 360, sat, val);
	return `rgb(${r}, ${g}, ${b})`;
}

// Format a price with color
function colorPriceHtml(price: number, precision: number = 1): string {
	const color = priceColor(price);
	return `<span style="color: ${color}">${price.toFixed(precision)}&cent;</span>`;
}

// Format a temperature with color
function colorTempHtml(temp: number, precision: number = 1): string {
	const color = tempColor(temp);
	return `<span style="color: ${color}"><b>${temp.toFixed(precision)}&deg;</b></span>`;
}

// Equivalent gas cost (matches htmltools.py)
function equivalentGasCost(electricityCostCents: number): number {
	const gasVehicleMpg = 49.0;
	const evEfficiency = 3.5;
	const conversionRate = gasVehicleMpg / evEfficiency;
	return Math.round((electricityCostCents * conversionRate) / 100 * 100) / 100;
}

// Variable delivery rate from most recent ComEd bill (Winter 2025-26)
const DELIVERY_CENTS_PER_KWH = 6.354;

// ===========================================================
// Stale data detection
// ===========================================================

const STALE_THRESHOLD_SECONDS = 300; // 5 minutes

function getAgeSeconds(generatedAt: string | undefined): number | null {
	if (!generatedAt) return null;
	const ts = new Date(generatedAt).getTime();
	if (isNaN(ts)) return null;
	return (Date.now() - ts) / 1000;
}

function isStale(generatedAt: string | undefined): boolean {
	const age = getAgeSeconds(generatedAt);
	if (age === null) return true; // missing or invalid = stale
	return age > STALE_THRESHOLD_SECONDS;
}

function formatAge(generatedAt: string | undefined): string {
	const age = getAgeSeconds(generatedAt);
	if (age === null) return "unknown";
	if (age < 60) return "just now";
	if (age < 3600) return `${Math.floor(age / 60)}m ago`;
	return `${Math.floor(age / 3600)}h ago`;
}

function updateTimestamp(elementId: string, generatedAt: string | undefined): void {
	const el = document.getElementById(elementId);
	if (!el) return;
	if (isStale(generatedAt)) {
		el.innerHTML = `<span class="stale-warning">stale - ${formatAge(generatedAt)}</span>`;
	} else {
		el.textContent = `updated ${formatAge(generatedAt)}`;
	}
}

// ===========================================================
// ComEd panel rendering
// ===========================================================

interface ComedSample {
	time_hour: number;
	time_min: number;
	price: number;
}

interface HourlyAvg {
	hour_start: number;
	hour_end: number;
	avg_price: number;
}

interface RawPrice {
	hours_since_midnight: number;
	price: number;
}

interface ComedData {
	generated_at: string;
	median_rate: number;
	median_std: number;
	current_rate: number;
	predicted_rate: number;
	cutoff_rate: number;
	recent_samples: ComedSample[];
	previous_samples: ComedSample[];
	hourly_averages: HourlyAvg[];
	raw_prices: RawPrice[];
}

function renderComed(data: ComedData): void {
	const container = document.getElementById("comed-content");
	if (!container) return;
	updateTimestamp("comed-timestamp", data.generated_at);

	let html = "";

	// Status header
	const medGas = equivalentGasCost(data.median_rate + DELIVERY_CENTS_PER_KWH);
	const stdGas = equivalentGasCost(data.median_std);
	const curGas = equivalentGasCost(data.current_rate + DELIVERY_CENTS_PER_KWH);
	const isOn = data.predicted_rate < data.cutoff_rate;

	html += `<div class="stat-row"><span class="stat-label">24hr Median Rate:</span> ${colorPriceHtml(data.median_rate)} &plusmn; ${data.median_std.toFixed(2)}&cent;</div>`;
	html += `<div class="stat-row"><span class="stat-label">&nbsp;Equivalent Gas Rate:</span> $${medGas.toFixed(2)} &plusmn; $${stdGas.toFixed(2)} per gallon</div>`;
	html += `<div class="stat-row"><span class="stat-label">Hour Current Rate:</span> ${colorPriceHtml(data.current_rate, 3)}</div>`;
	html += `<div class="stat-row"><span class="stat-label">&nbsp;Equivalent Gas Rate:</span> $${curGas.toFixed(2)} per gallon</div>`;
	html += `<div class="stat-row"><span class="stat-label">Hour Predict Rate:</span> ${colorPriceHtml(data.predicted_rate, 3)}</div>`;
	html += `<div class="stat-row"><span class="stat-label">Usage CutOff Rate:</span> ${colorPriceHtml(data.cutoff_rate, 3)}</div>`;

	const badgeClass = isOn ? "status-on" : "status-off";
	const badgeText = isOn ? "*ON*" : ".OFF.";
	html += `<div class="stat-row">House Usage Status: <span class="status-badge ${badgeClass}">${badgeText}</span></div>`;

	// Tables side by side
	html += `<div class="tables-row">`;

	// Recent rates table
	html += `<table><tr><th colspan="2">Recent Rates</th></tr>`;
	html += `<tr><th>Time</th><th>Cost</th></tr>`;
	for (const s of data.recent_samples) {
		const min = s.time_min.toString().padStart(2, "0");
		html += `<tr><td>${s.time_hour}:${min}</td><td>${colorPriceHtml(s.price)}</td></tr>`;
	}
	for (const s of data.previous_samples) {
		const min = s.time_min.toString().padStart(2, "0");
		html += `<tr class="row-previous"><td>${s.time_hour}:${min}</td><td>${colorPriceHtml(s.price)}</td></tr>`;
	}
	html += `</table>`;

	// Hourly averages table
	html += `<table><tr><th colspan="2">Hourly Averages</th></tr>`;
	html += `<tr><th>Range</th><th>Cost</th></tr>`;
	for (const h of data.hourly_averages) {
		let start = h.hour_start;
		let end = h.hour_end;
		let rowClass = "";
		if (end < 1) {
			start += 24;
			end += 24;
			rowClass = "row-past";
		}
		html += `<tr class="${rowClass}"><td>${start}-${end}:00</td><td>${colorPriceHtml(h.avg_price, 2)}</td></tr>`;
	}
	html += `</table>`;

	html += `</div>`; // tables-row

	// Chart canvas
	html += `<div class="chart-container"><canvas id="price-chart"></canvas></div>`;

	container.innerHTML = html;

	// Render Chart.js chart
	renderPriceChart(data);
}

function renderPriceChart(data: ComedData): void {
	const canvas = document.getElementById("price-chart") as HTMLCanvasElement | null;
	if (!canvas) return;

	const dark = isDarkMode();
	const gridColor = dark ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.1)";
	const tickColor = dark ? "#bbbbbb" : "#666666";

	// Raw 5-min prices as scatter
	const scatterData = data.raw_prices.map(p => ({ x: p.hours_since_midnight, y: p.price }));

	// Hourly averages as line (sort by hour ascending)
	const sortedAvgs = [...data.hourly_averages].sort((a, b) => a.hour_start - b.hour_start);
	const lineData = sortedAvgs.map(h => ({
		x: (h.hour_start + h.hour_end) / 2,
		y: h.avg_price,
	}));

	// Determine axis bounds
	const allPrices = data.raw_prices.map(p => p.price);
	const maxPrice = Math.max(4, ...allPrices) + 0.5;

	new (window as any).Chart(canvas, {
		type: "scatter",
		data: {
			datasets: [
				{
					label: "5-min prices",
					data: scatterData,
					pointBackgroundColor: dark ? "#44cc44" : "#006400",
					pointBorderColor: "transparent",
					pointRadius: 3,
					showLine: false,
					order: 2,
				},
				{
					label: "Hourly average",
					data: lineData,
					borderColor: dark ? "#6699ff" : "#00008b",
					backgroundColor: "transparent",
					pointRadius: 0,
					borderWidth: 2,
					showLine: true,
					order: 1,
				},
			],
		},
		options: {
			responsive: true,
			maintainAspectRatio: true,
			aspectRatio: 0.75,
			plugins: {
				legend: {
					labels: { color: tickColor },
				},
				tooltip: {
					callbacks: {
						label: function(ctx: any) {
							const h = Math.floor(ctx.parsed.x);
							const m = Math.round((ctx.parsed.x - h) * 60);
							return `${h}:${m.toString().padStart(2, "0")} - ${ctx.parsed.y.toFixed(2)} cents`;
						},
					},
				},
			},
			scales: {
				x: {
					type: "linear",
					min: 0,
					max: 24,
					ticks: {
						stepSize: 1,
						color: tickColor,
						callback: function(val: number) {
							if (val <= 12) return val + "a";
							if (val === 12) return "12p";
							return (val - 12) + "p";
						},
					},
					title: { display: true, text: "Time (hours)", color: tickColor },
					grid: { color: gridColor },
				},
				y: {
					min: 0,
					max: maxPrice,
					ticks: { color: tickColor },
					title: { display: true, text: "Cents per kWh", color: tickColor },
					grid: { color: gridColor },
				},
			},
		},
	});
}

// ===========================================================
// Ecobee panel rendering
// ===========================================================

interface EcobeeData {
	generated_at: string;
	cool_setting: number;
	heat_setting: number;
	sensors: { [name: string]: { temperature?: number; humidity?: number } };
	avg_temperature: number | null;
	std_temperature: number | null;
	avg_humidity: number | null;
}

function renderEcobee(data: EcobeeData): void {
	const container = document.getElementById("ecobee-content");
	if (!container) return;
	updateTimestamp("ecobee-timestamp", data.generated_at);

	let html = "";

	// Settings
	html += `<div class="stat-row">Cool Setting: ${colorTempHtml(data.cool_setting)}</div>`;
	html += `<div class="stat-row">Heat Setting: ${colorTempHtml(data.heat_setting)}</div>`;

	// Sensors
	html += `<div class="sensor-grid">`;
	for (const [name, sensor] of Object.entries(data.sensors)) {
		const tempStr = sensor.temperature !== undefined
			? colorTempHtml(sensor.temperature)
			: "N/A";
		html += `<div class="sensor-item"><span>${name}</span> ${tempStr}</div>`;
	}
	html += `</div>`;

	// Averages
	if (data.avg_temperature !== null) {
		const stdStr = data.std_temperature !== null ? ` &plusmn; ${data.std_temperature.toFixed(2)}` : "";
		html += `<div class="stat-row">Average: ${colorTempHtml(data.avg_temperature)}${stdStr}</div>`;
	}
	if (data.avg_humidity !== null) {
		html += `<div class="stat-row">Humidity: ${data.avg_humidity.toFixed(0)}%</div>`;
	}

	container.innerHTML = html;
}

// ===========================================================
// Solar panel rendering
// ===========================================================

interface SolarData {
	generated_at: string;
	is_daytime: boolean;
	readings: { [key: string]: { value: number; unit: string } };
}

function renderSolar(data: SolarData): void {
	const container = document.getElementById("solar-content");
	if (!container) return;
	updateTimestamp("solar-timestamp", data.generated_at);

	let html = "";

	if (!data.is_daytime) {
		html += `<div class="stat-row" style="color: var(--text-muted)">Nighttime - no solar production</div>`;
	}

	const entries = Object.entries(data.readings);
	if (entries.length === 0 && data.is_daytime) {
		html += `<div class="stat-row" style="color: var(--text-muted)">No active readings</div>`;
	}

	for (const [key, val] of entries) {
		const kValue = (val.value / 1000).toFixed(3);
		html += `<div class="stat-row">${key}: ${kValue} k${val.unit}</div>`;
	}

	container.innerHTML = html;
}

// ===========================================================
// Data fetching
// ===========================================================

function showError(containerId: string, message: string): void {
	const el = document.getElementById(containerId);
	if (el) {
		el.innerHTML = `<div class="error">${message}</div>`;
	}
}

async function fetchJson<T>(url: string): Promise<T | null> {
	const response = await fetch(url);
	if (!response.ok) return null;
	return await response.json() as T;
}

async function loadDashboard(): Promise<void> {
	// Fetch all three data sources in parallel
	const [comedResult, ecobeeResult, solarResult] = await Promise.allSettled([
		fetchJson<ComedData>("api/comed.json"),
		fetchJson<EcobeeData>("api/ecobee.json"),
		fetchJson<SolarData>("api/solar.json"),
	]);

	// ComEd
	if (comedResult.status === "fulfilled" && comedResult.value) {
		renderComed(comedResult.value);
	} else {
		showError("comed-content", "ComEd data unavailable");
	}

	// Ecobee
	if (ecobeeResult.status === "fulfilled" && ecobeeResult.value) {
		renderEcobee(ecobeeResult.value);
	} else {
		showError("ecobee-content", "Ecobee data unavailable");
	}

	// Solar
	if (solarResult.status === "fulfilled" && solarResult.value) {
		renderSolar(solarResult.value);
	} else {
		showError("solar-content", "Solar data unavailable");
	}
}

// Run on page load
loadDashboard();
