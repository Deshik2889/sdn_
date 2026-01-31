function createChart(id, datasetsConfig) {
    const datasets = datasetsConfig.map(cfg => ({
        label: cfg.label,
        data: [],
        borderColor: cfg.color,
        borderWidth: cfg.borderWidth || 2,
        borderDash: cfg.borderDash || [],
        pointStyle: cfg.pointStyle || 'circle',
        tension: 0.35,
        pointRadius: 3
    }));

    return new Chart(document.getElementById(id), {
        type: 'line',
        data: {
            labels: [],
            datasets: datasets
        },
        options: {
            animation: false,
            plugins: {
                legend: { labels: { color: '#00f7ff' } }
            },
            scales: {
                x: { ticks: { color: '#00f7ff' } },
                y: { ticks: { color: '#00f7ff' } }
            }
        }
    });
}

const tChart = createChart("throughputChart", [
    {label: 'Baseline Throughput', color: '#00f7ff'},
    {label: 'Proposed Throughput', color: '#00ff9c', borderDash: [6,4], borderWidth: 3, pointStyle: 'rect'}
]);
const lChart = createChart("latencyChart", [
    {label: 'Baseline Latency', color: '#ff9f00'},
    {label: 'Proposed Latency', color: '#ffd86b'}
]);
const pChart = createChart("lossChart", [
    {label: 'Baseline Packet Loss', color: '#ff004c'},
    {label: 'Proposed Packet Loss', color: '#ff8aa0'}
]);
const eChart = createChart("ewmaChart", [
    {label: 'EWMA Utilization (%)', color: '#00ff9c'}
]);

// New: flows chart (single dataset)
const fChart = createChart("flowsChart", [
    {label: 'Flows', color: '#8ea6ff'}
]);

// top ports bar chart
function createBarChart(id, label, color) {
    return new Chart(document.getElementById(id), {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                backgroundColor: color
            }]
        },
        options: {
            animation: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: '#00f7ff' } },
                y: { ticks: { color: '#00f7ff' } }
            }
        }
    });
}

const topPortsChart = createBarChart('topPortsChart', 'Top Ports Utilization', '#ff7a7a');

function update(chart, ...values) {
    chart.data.labels.push(new Date().toLocaleTimeString());
    for (let i = 0; i < chart.data.datasets.length; i++) {
        const v = values[i] !== undefined ? values[i] : values[0];
        chart.data.datasets[i].data.push(v);
        if (chart.data.datasets[i].data.length > 25) {
            chart.data.datasets[i].data.shift();
        }
    }
    if (chart.data.labels.length > 25) chart.data.labels.shift();
    chart.update();
}

function updateStatus(state, mode) {
    const el = document.getElementById("status");
    el.className = "status " +
        (state === "SAFE" ? "safe" :
        state === "PREDICTED_CONGESTION" ? "warn" : "danger");
    el.innerText = `${state} | ${mode.toUpperCase()}`;
}

// Mode switch with debounce: disable the button briefly to avoid accidental double-clicks
function setMode(mode) {
    const btnId = mode === 'proposed' ? null : null; // placeholder if we want per-button behavior
    // perform mode change
    fetch(`/api/mode/${mode}`).then(() => {
        // temporarily disable both mode buttons for 2s
        const btns = Array.from(document.querySelectorAll('.header .btn'))
            .filter(b => b.innerText.trim().toLowerCase() === 'baseline' || b.innerText.trim().toLowerCase() === 'proposed');
        btns.forEach(b => b.disabled = true);
        setTimeout(() => btns.forEach(b => b.disabled = false), 2000);
    }).catch(err => {
        console.error('Failed to set mode', err);
        alert('Failed to change mode');
    });
}

let pollInterval = null;

function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(() => {
        fetch("/api/metrics")
            .then(r => r.json())
            .then(d => {
                update(tChart, d.throughput_baseline, d.throughput_proposed);
                update(lChart, d.latency_baseline, d.latency_proposed);
                update(pChart, d.packet_loss_baseline, d.packet_loss_proposed);
                // EWMA in percent if available, otherwise fallback
                const ew = d.ewma_percent !== undefined ? d.ewma_percent : (d.ewma ? d.ewma * 100 : 0);
                update(eChart, ew);
                update(fChart, d.flows || 0);
                // update top ports bar chart
                const tp = d.top_ports || [];
                const labels = tp.map(x => x.port);
                const vals = tp.map(x => Math.round(x.utilization * 100));
                updateBar(topPortsChart, labels, vals);
                updateStatus(d.state, d.mode);
            });
    }, 2000);
}

function stopPolling() {
    if (!pollInterval) return;
    clearInterval(pollInterval);
    pollInterval = null;
}

// Start/stop traffic via backend and toggle polling
function startTraffic() {
    fetch('/api/start-traffic')
        .then(() => {
            startPolling();
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
        });
}

function stopTraffic() {
    fetch('/api/stop')
        .then(() => {
            stopPolling();
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        });
}

function updateBar(chart, labels, values) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
}

// On load: if traffic already running, start polling automatically
window.addEventListener('load', () => {
    fetch('/api/traffic-status')
        .then(r => r.json())
        .then(j => {
            if (j.running) startPolling();
            document.getElementById('startBtn').disabled = j.running;
            document.getElementById('stopBtn').disabled = !j.running;
        });
});

function exportCharts() {
    const items = [
        {chart: tChart, name: 'throughput.png'},
        {chart: lChart, name: 'latency.png'},
        {chart: pChart, name: 'packet_loss.png'},
        {chart: eChart, name: 'ewma.png'}
    ];

    const promises = items.map(it => new Promise(resolve => {
        it.chart.canvas.toBlob(blob => {
            resolve({name: it.name, blob});
        }, 'image/png');
    }));

    Promise.all(promises).then(results => {
        const form = new FormData();
        results.forEach((r, idx) => form.append(`file${idx}`, r.blob, r.name));

        fetch('/api/save-charts', {method: 'POST', body: form})
            .then(res => res.json())
            .then(j => {
                alert('Saved charts: ' + j.saved.join('\n'));
            })
            .catch(err => {
                console.error(err);
                alert('Failed to save charts');
            });
    });
}

// -------------------- Topology viz using vis-network --------------------
let topologyNetwork = null;
let topologyNodes = null;
let topologyEdges = null;

function initTopology() {
    const container = document.getElementById('topology');
    topologyNodes = new vis.DataSet();
    topologyEdges = new vis.DataSet();
    const data = { nodes: topologyNodes, edges: topologyEdges };
    const options = {
        nodes: { color: { background: '#072027', border: '#00f7ff' }, font: { color: '#00f7ff' } },
        edges: { color: '#888', width: 2, smooth: true },
        physics: { stabilization: false, barnesHut: { gravitationalConstant: -3000 } },
        interaction: { hover: true }
    };
    topologyNetwork = new vis.Network(container, data, options);
}

function refreshTopology() {
    fetch('/api/topology')
        .then(r => r.json())
        .then(j => {
            // nodes
            const nodes = (j.nodes || []).map(n => ({ id: n.id, label: n.label }));
            topologyNodes.update(nodes);

            // edges
            const edges = (j.links || []).map(l => {
                // default color
                let color = { color: '#888' };
                if (l.congested) color = { color: '#ff4d4d' };
                // if rerouted_links include link id, mark blue
                const rer = (j.rerouted_links || []).includes(l.id);
                if (rer) color = { color: '#4da6ff' };
                return {
                    id: l.id,
                    from: l.from,
                    to: l.to,
                    label: `${Math.round(l.utilization*100)}%`,
                    color: color,
                    width: rer ? 4 : (l.congested ? 3 : 2)
                };
            });

            // replace edges dataset
            topologyEdges.clear();
            topologyEdges.add(edges);
        })
        .catch(err => { /* silently ignore until topology available */ });
}

// start topology on load
window.addEventListener('load', () => {
    initTopology();
    // refresh every 2s
    setInterval(refreshTopology, 2000);
});
