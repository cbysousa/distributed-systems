let sources = [];
let metricsBySourceType = {};

async function refreshAll() {
    await loadSources();
    await loadReadings();
}

async function loadSources() {
    const response = await fetch("/api/sources");
    const data = await response.json();

    if (!data.success) {
        alert(data.message || "Erro ao carregar fontes.");
        return;
    }

    sources = data.sources;
    metricsBySourceType = data.metrics_by_source_type;

    renderSourcesTable();
    renderSourceOptions();
    renderMetricOptions();
    renderControlPanel();
}

function renderSourcesTable() {
    const table = document.getElementById("sourcesTable");
    table.innerHTML = "";

    for (const source of sources) {
        const statusClass = source.status === "OFFLINE" ? "status-offline" : "status-active";

        table.innerHTML += `
            <tr>
                <td>${source.name}</td>
                <td>${source.source_type}</td>
                <td class="${statusClass}">${source.status}</td>
                <td>${source.controllable ? "sim" : "não"}</td>
                <td>${source.address || "-"}</td>
            </tr>
        `;
    }
}

function renderSourceOptions() {
    const select = document.getElementById("sourceSelect");
    const previousValue = select.value;

    select.innerHTML = "";

    for (const source of sources) {
        const option = document.createElement("option");
        option.value = source.name;
        option.textContent = `${source.name} (${source.source_type})`;
        select.appendChild(option);
    }

    if (previousValue) {
        select.value = previousValue;
    }

    select.onchange = async () => {
        hideCommandResult();
        renderMetricOptions();
        renderControlPanel();
        await loadReadings();
    };
}

function getSelectedSource() {
    const sourceName = document.getElementById("sourceSelect").value;
    return sources.find(item => item.name === sourceName);
}

function renderControlPanel() {
    const source = getSelectedSource();
    const unavailable = document.getElementById("controlUnavailable");
    const lamppostControls = document.getElementById("lamppostControls");

    unavailable.classList.add("hidden");
    lamppostControls.classList.add("hidden");

    if (!source) {
        hideCommandResult();
        unavailable.textContent = "Nenhuma fonte selecionada.";
        unavailable.classList.remove("hidden");
        return;
    }

    if (!source.controllable) {
        hideCommandResult();
        unavailable.textContent = `${source.name} e uma fonte continua e nao recebe comandos de controle.`;
        unavailable.classList.remove("hidden");
        return;
    }

    if (source.source_type === "lamppost") {
        lamppostControls.classList.remove("hidden");
        return;
    }

    hideCommandResult();
    unavailable.textContent = `${source.name} e controlavel, mas nao ha comandos configurados para este tipo.`;
    unavailable.classList.remove("hidden");
}

function renderMetricOptions() {
    const sourceName = document.getElementById("sourceSelect").value;
    const source = sources.find(item => item.name === sourceName);
    const select = document.getElementById("metricSelect");

    select.innerHTML = "";

    if (!source) {
        return;
    }

    const metrics = metricsBySourceType[source.source_type] || [];

    for (const metric of metrics) {
        const option = document.createElement("option");
        option.value = metric;
        option.textContent = metric;
        select.appendChild(option);
    }

    select.onchange = loadReadings;
}

async function loadReadings() {
    const source = document.getElementById("sourceSelect").value;
    const metric = document.getElementById("metricSelect").value;

    if (!source || !metric) {
        return;
    }

    const params = new URLSearchParams({
        source: source,
        metric: metric,
    });

    const response = await fetch(`/api/readings?${params.toString()}`);
    const data = await response.json();

    if (!data.success) {
        alert(data.message || "Erro ao carregar leituras.");
        return;
    }

    const readings = data.readings.slice(-100);

    renderReadingsTable(readings);
    drawChart(readings);
}

function renderReadingsTable(readings) {
    const table = document.getElementById("readingsTable");
    table.innerHTML = "";

    const lastReadings = readings.slice(-15).reverse();

    for (const reading of lastReadings) {
        table.innerHTML += `
            <tr>
                <td>${reading.source_name}</td>
                <td>${reading.source_type}</td>
                <td>${reading.metric}</td>
                <td>${reading.value.toFixed(2)}</td>
                <td>${reading.unit}</td>
                <td>${formatTime(reading.timestamp_unix_ms)}</td>
            </tr>
        `;
    }
}

function drawChart(readings) {
    const canvas = document.getElementById("chart");
    const ctx = canvas.getContext("2d");
    const message = document.getElementById("chartMessage");

    const rect = canvas.getBoundingClientRect();
    const scale = window.devicePixelRatio || 1;

    canvas.width = rect.width * scale;
    canvas.height = rect.height * scale;
    ctx.scale(scale, scale);

    const width = rect.width;
    const height = rect.height;

    ctx.clearRect(0, 0, width, height);

    if (!readings || readings.length < 2) {
        message.classList.remove("hidden");
        message.textContent = "Ainda não há leituras suficientes para desenhar a série temporal.";
        return;
    }

    message.classList.add("hidden");

    const paddingLeft = 55;
    const paddingRight = 20;
    const paddingTop = 20;
    const paddingBottom = 45;

    const chartWidth = width - paddingLeft - paddingRight;
    const chartHeight = height - paddingTop - paddingBottom;

    const values = readings.map(item => item.value);
    let minValue = Math.min(...values);
    let maxValue = Math.max(...values);

    if (minValue === maxValue) {
        minValue -= 1;
        maxValue += 1;
    }

    function xPosition(index) {
        return paddingLeft + (index / (readings.length - 1)) * chartWidth;
    }

    function yPosition(value) {
        return paddingTop + ((maxValue - value) / (maxValue - minValue)) * chartHeight;
    }

    ctx.strokeStyle = "#d1d5db";
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.moveTo(paddingLeft, paddingTop);
    ctx.lineTo(paddingLeft, paddingTop + chartHeight);
    ctx.lineTo(paddingLeft + chartWidth, paddingTop + chartHeight);
    ctx.stroke();

    ctx.fillStyle = "#374151";
    ctx.font = "12px Arial";
    ctx.fillText(maxValue.toFixed(2), 8, paddingTop + 8);
    ctx.fillText(minValue.toFixed(2), 8, paddingTop + chartHeight);

    ctx.fillText(formatTime(readings[0].timestamp_unix_ms), paddingLeft, height - 14);
    ctx.fillText(formatTime(readings[readings.length - 1].timestamp_unix_ms), paddingLeft + chartWidth - 55, height - 14);

    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 2;
    ctx.beginPath();

    readings.forEach((reading, index) => {
        const x = xPosition(index);
        const y = yPosition(reading.value);

        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.stroke();

    ctx.fillStyle = "#2563eb";

    readings.forEach((reading, index) => {
        const x = xPosition(index);
        const y = yPosition(reading.value);

        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
    });
}

async function runAggregate() {
    const source = document.getElementById("sourceSelect").value;
    const metric = document.getElementById("metricSelect").value;
    const operation = document.getElementById("operationSelect").value;
    const windowSeconds = Number(document.getElementById("windowInput").value || 0);

    const response = await fetch("/api/aggregate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            source_name: source,
            metric: metric,
            operation: operation,
            window_seconds: windowSeconds,
        }),
    });

    const data = await response.json();
    const result = document.getElementById("aggregateResult");

    result.classList.remove("hidden");

    if (!data.success || !data.aggregate) {
        result.textContent = data.message || "Erro na consulta agregada.";
        return;
    }

    result.textContent =
        `Resultado: ${data.aggregate.value.toFixed(4)} ${data.aggregate.unit || ""} ` +
        `(${data.aggregate.sample_count} amostras)`;
}

async function lamppostCommand(action) {
    const selectedSource = getSelectedSource();

    if (!selectedSource || selectedSource.source_type !== "lamppost" || !selectedSource.controllable) {
        await showCommandResult({
            success: false,
            message: "Selecione uma fonte controlavel do tipo lamppost.",
        });
        return;
    }

    const source = selectedSource.name;

    const response = await fetch(`/api/lamppost/${source}/${action}`, {
        method: "POST",
    });

    const data = await response.json();

    await showCommandResult(data);
    await refreshAll();
}

async function setLuminosity() {
    const selectedSource = getSelectedSource();

    if (!selectedSource || selectedSource.source_type !== "lamppost" || !selectedSource.controllable) {
        await showCommandResult({
            success: false,
            message: "Selecione uma fonte controlavel do tipo lamppost.",
        });
        return;
    }

    const source = selectedSource.name;
    const luminosity = Number(document.getElementById("luminosityInput").value || 0);

    const response = await fetch(`/api/lamppost/${source}/luminosity`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            luminosity_percent: luminosity,
        }),
    });

    const data = await response.json();

    await showCommandResult(data);
    await refreshAll();
}

async function showCommandResult(data) {
    const result = document.getElementById("commandResult");
    result.classList.remove("hidden");

    if (data.command) {
        const source = getSelectedSource();
        const latestReadings = source ? await loadLatestReadingsByMetric(source.name) : {};
        renderCommandSnapshot(result, data.command, source, latestReadings);
    } else {
        result.textContent = data.message || "Comando executado.";
    }
}

function hideCommandResult() {
    const result = document.getElementById("commandResult");
    result.classList.add("hidden");
    result.textContent = "";
}

async function loadLatestReadingsByMetric(sourceName) {
    const params = new URLSearchParams({ source: sourceName });
    const response = await fetch(`/api/readings?${params.toString()}`);
    const data = await response.json();
    const latest = {};

    if (!data.success) {
        return latest;
    }

    for (const reading of data.readings) {
        latest[reading.metric] = reading;
    }

    return latest;
}

function renderCommandSnapshot(container, command, source, readings) {
    const lightState = command.light_on ? "acesa" : "apagada";
    const energy = readings.energy_consumption_kwh;
    const lastSeen = source?.last_seen_unix_ms ? formatTime(source.last_seen_unix_ms) : "-";

    container.innerHTML = `
        <div class="status-summary">
            <strong>${command.message}</strong>
            <dl>
                <div>
                    <dt>Fonte</dt>
                    <dd>${source?.name || "-"}</dd>
                </div>
                <div>
                    <dt>Status</dt>
                    <dd>${command.source_status || source?.status || "-"}</dd>
                </div>
                <div>
                    <dt>Luz</dt>
                    <dd>${lightState}</dd>
                </div>
                <div>
                    <dt>Brilho</dt>
                    <dd>${command.luminosity_percent.toFixed(0)}%</dd>
                </div>
                <div>
                    <dt>Consumo</dt>
                    <dd>${energy ? `${energy.value.toFixed(4)} ${energy.unit}` : "-"}</dd>
                </div>
                <div>
                    <dt>Endereco TCP</dt>
                    <dd>${source?.address || "-"}</dd>
                </div>
                <div>
                    <dt>Ultima descoberta</dt>
                    <dd>${lastSeen}</dd>
                </div>
            </dl>
        </div>
    `;
}

function formatTime(timestampUnixMs) {
    if (!timestampUnixMs || timestampUnixMs <= 0) {
        return "-";
    }

    const date = new Date(timestampUnixMs);
    return date.toLocaleTimeString("pt-BR");
}

window.addEventListener("resize", loadReadings);

refreshAll();
setInterval(loadReadings, 5000);
