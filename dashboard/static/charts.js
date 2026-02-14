function createChart(id, datasetsConfig) {
    const datasets = datasetsConfig.map(cfg => ({
        label: cfg.label,
        data: [],
        borderColor: cfg.color,
        yAxisID: cfg.yAxisID || 'y',
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

// Unified metrics chart with baseline/proposed datasets for clearer comparison
const unifiedChart = createChart("unifiedMetricsChart", [
    {label: 'Throughput (Baseline, Mbps)', color: '#00d0ff', borderDash: [6,4], yAxisID: 'y'},
    {label: 'Throughput (Proposed, Mbps)', color: '#00a0ff', borderDash: [], yAxisID: 'y'},
    {label: 'Latency (Baseline, ms)', color: '#ffbf6b', borderDash: [6,4], yAxisID: 'y1'},
    {label: 'Latency (Proposed, ms)', color: '#ff9f00', borderDash: [], yAxisID: 'y1'},
    {label: 'Packet Loss (Baseline, %)', color: '#ff7a96', borderDash: [6,4], yAxisID: 'y1'},
    {label: 'Packet Loss (Proposed, %)', color: '#ff004c', borderDash: [], yAxisID: 'y1'},
    {label: 'EWMA (%)', color: '#00ff9c', borderDash: [], yAxisID: 'ewma', borderWidth: 3}
]);

// Configure unified chart with dual Y-axes
unifiedChart.options.scales = {
    x: { ticks: { color: '#00f7ff' } },
    y: { 
        type: 'linear',
        position: 'left',
        ticks: { color: '#00f7ff' },
        title: { display: true, text: 'Throughput (Mbps)', color: '#00f7ff' }
    },
    y1: { 
        type: 'linear',
        position: 'right',
        ticks: { color: '#ff9f00' },
        title: { display: true, text: 'Latency / Packet Loss', color: '#ff9f00' },
        grid: { drawOnChartArea: false }
    },
    ewma: {
        type: 'linear',
        position: 'right',
        ticks: { color: '#00ff9c' },
        title: { display: true, text: 'EWMA (%)', color: '#00ff9c' },
        grid: { drawOnChartArea: false },
        min: 0,
        max: 100
    }
};
unifiedChart.update();
// track current UI mode to highlight buttons and control reroute display
let CURRENT_MODE = 'baseline';

function applyModeVisuals(mode){
    CURRENT_MODE = mode;
    const bBase = document.getElementById('baselineBtn');
    const bProp = document.getElementById('proposedBtn');
    if(bBase) bBase.classList.toggle('active', mode === 'baseline');
    if(bProp) bProp.classList.toggle('active', mode === 'proposed');
    // update status text immediately for clarity
    const st = document.getElementById('status');
    if(st) st.innerText = `${st.innerText.split('|')[0].trim()} | ${mode.toUpperCase()}`;
}

// Show/hide datasets so baseline/proposed are exclusive (EWMA stays visible)
function setChartModeVisibility(mode){
    // dataset order: 0:thr_base,1:thr_prop,2:lat_base,3:lat_prop,4:pl_base,5:pl_prop,6:ewma
    if(!unifiedChart || !unifiedChart.data || !unifiedChart.data.datasets) return;
    const ds = unifiedChart.data.datasets;
    const showBaseline = mode === 'baseline';
    // throughput
    if(ds[0]) ds[0].hidden = !showBaseline;
    if(ds[1]) ds[1].hidden = showBaseline;
    // latency
    if(ds[2]) ds[2].hidden = !showBaseline;
    if(ds[3]) ds[3].hidden = showBaseline;
    // packet loss
    if(ds[4]) ds[4].hidden = !showBaseline;
    if(ds[5]) ds[5].hidden = showBaseline;
    // EWMA always visible
    if(ds[6]) ds[6].hidden = false;
    unifiedChart.update();
}

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
    console.log('Setting mode to:', mode);
    const btnId = mode === 'proposed' ? null : null; // placeholder if we want per-button behavior
    // perform mode change
    fetch(`/api/mode/${mode}`)
        .then(response => {
            console.log('Mode change response:', response);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Mode changed to:', data);
            // visually apply active state
            applyModeVisuals(mode);
            setChartModeVisibility(mode);
            // temporarily disable both mode buttons for 1s to avoid double clicks
            const btns = [document.getElementById('baselineBtn'), document.getElementById('proposedBtn')].filter(Boolean);
            btns.forEach(b => b.disabled = true);
            setTimeout(() => btns.forEach(b => b.disabled = false), 1000);
        })
        .catch(error => {
            console.error('Error changing mode:', error);
            alert('Error changing mode: ' + error.message);
        });
}

let pollInterval = null;

// track congestion marker datasets so we can clear them on stop
let congestionMarkersCount = 0;
// track last reported backend state so we can add markers on transitions
let last_state = null;

function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(() => {
        fetch("/api/metrics")
            .then(r => r.json())
            .then(d => {
                console.log('Metrics data received:', d);
                  // EWMA in percent if available, otherwise fallback
                  const ew = d.ewma_percent !== undefined ? d.ewma_percent : (d.ewma ? d.ewma * 100 : 0);

                  // Update unified chart with baseline/proposed series order matching initialization
                  // [throughput_base, throughput_prop, latency_base, latency_prop, pl_base, pl_prop, ewma]
                  update(unifiedChart,
                      d.throughput_baseline || d.throughput || 0,
                      d.throughput_proposed || d.throughput || 0,
                      d.latency_baseline || 0,
                      d.latency_proposed || 0,
                      d.packet_loss_baseline || 0,
                      d.packet_loss_proposed || 0,
                      ew);
                
                update(fChart, d.flows || 0);
                // update top ports bar chart
                const tp = d.top_ports || [];
                const labels = tp.map(x => x.port);
                const vals = tp.map(x => Math.round(x.utilization * 100));
                updateBar(topPortsChart, labels, vals);
                updateStatus(d.state, d.mode);
                // reflect backend mode in UI visuals (in case changed elsewhere)
                if(d.mode) applyModeVisuals(d.mode);
                // add a congestion marker when backend state transitions to predicted/congested
                try {
                    if (last_state === null) last_state = d.state;
                    if (d.state !== last_state) {
                        if (d.state === 'PREDICTED_CONGESTION' || d.state === 'CONGESTED') {
                            addCongestionMarker(new Date());
                        }
                        last_state = d.state;
                    }
                } catch (e) {
                    console.error('State transition handling failed:', e);
                }
            })
            .catch(err => {
                console.log('Metrics fetch failed:', err);
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
    console.log('Starting traffic...');
    fetch('/api/start-traffic', { 
        method: 'GET',
        signal: AbortSignal.timeout(5000) // 5 second timeout
    })
        .then(response => {
            console.log('Start traffic response:', response);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Traffic started:', data);
            startPolling();
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
        })
        .catch(error => {
            console.error('Error starting traffic:', error);
            alert('Error starting traffic: ' + error.message);
        });
}

function stopTraffic() {
    console.log('Stopping traffic...');
    fetch('/api/stop')
        .then(response => {
            console.log('Stop traffic response:', response);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Traffic stopped:', data);
            stopPolling();
            const sb = document.getElementById('stopBtn');
            if (sb) sb.disabled = true;
            // Keep congestion markers visible after stopping so the graph shows
            // where congestion was triggered during the run. Markers persist
            // until the page is refreshed or the user manually exports/clears charts.
        })
        .catch(error => {
            console.error('Error stopping traffic:', error);
            alert('Error stopping traffic: ' + error.message);
        });
}

function congest() {
    console.log('Creating congestion...');
    fetch('/api/congest')
        .then(response => {
            console.log('Congest response:', response);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Congestion created:', data);
            alert('Congestion created successfully');
            try {
                // add a vertical marker at the current time to the unified chart
                const now = new Date();
                addCongestionMarker(now);
            } catch (e) {
                console.error('Failed to add congestion marker:', e);
            }
        })
        .catch(error => {
            console.error('Error creating congestion:', error);
            alert('Error creating congestion: ' + error.message);
        });
}

function updateBar(chart, labels, values) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();
}

// Add a vertical dashed line marker at a given timestamp on the unified chart
function addCongestionMarker(time) {
    if (!unifiedChart || !unifiedChart.scales || !unifiedChart.scales.y) return;
    const yScale = unifiedChart.scales.y;
    const yMin = (typeof yScale.min === 'number') ? yScale.min : (Math.min(...(unifiedChart.data.datasets[0].data || [0])) || 0);
    const yMax = (typeof yScale.max === 'number') ? yScale.max : (Math.max(...(unifiedChart.data.datasets[1].data || [1])) || 1);

    const timeLabel = (time instanceof Date) ? time.toLocaleTimeString() : String(time);
    const markerDataset = {
        label: `CONGEST ${++congestionMarkersCount}`,
        data: [
            { x: timeLabel, y: yMin },
            { x: timeLabel, y: yMax }
        ],
        borderColor: 'rgba(255,60,60,0.95)',
        borderWidth: 2,
        pointRadius: 0,
        borderDash: [6, 4],
        fill: false,
        tension: 0,
        yAxisID: 'y',
        order: 999,
        // custom flag so we can remove these later
        isMarker: true
    };

    unifiedChart.data.datasets.push(markerDataset);
    unifiedChart.update();

    // Also add markers on flows and top ports charts to align the timestamp
    try {
        const timeLabel = (time instanceof Date) ? time.toLocaleTimeString() : String(time);
        // flows chart marker
        if (fChart && fChart.data) {
            const fMin = 0;
            const fMax = Math.max(...(fChart.data.datasets[0].data || [1]));
            const fMarker = {
                label: markerDataset.label,
                data: [{ x: timeLabel, y: fMin }, { x: timeLabel, y: fMax }],
                borderColor: markerDataset.borderColor,
                borderWidth: markerDataset.borderWidth,
                pointRadius: 0,
                borderDash: markerDataset.borderDash,
                fill: false,
                tension: 0,
                type: 'line',
                yAxisID: undefined,
                isMarker: true,
                order: 999
            };
            fChart.data.datasets.push(fMarker);
            fChart.update();
        }

        // top ports chart marker (bar chart) - add a line dataset overlay
        if (topPortsChart && topPortsChart.data) {
            const tpMin = 0;
            const tpMax = Math.max(...(topPortsChart.data.datasets[0].data || [1]));
            const tpMarker = {
                label: markerDataset.label,
                data: [{ x: timeLabel, y: tpMin }, { x: timeLabel, y: tpMax }],
                borderColor: markerDataset.borderColor,
                borderWidth: markerDataset.borderWidth,
                pointRadius: 0,
                borderDash: markerDataset.borderDash,
                fill: false,
                tension: 0,
                type: 'line',
                isMarker: true,
                order: 999
            };
            topPortsChart.data.datasets.push(tpMarker);
            topPortsChart.update();
        }
    } catch (e) {
        console.error('Failed to add markers to other charts:', e);
    }
}

function clearMarkers() {
    try {
        [unifiedChart, fChart, topPortsChart].forEach(ch => {
            if (!ch || !ch.data || !ch.data.datasets) return;
            ch.data.datasets = ch.data.datasets.filter(ds => !ds.isMarker);
            ch.update();
        });
        congestionMarkersCount = 0;
    } catch (e) {
        console.error('Failed to clear markers:', e);
    }
}

// On load: if traffic already running, start polling automatically
window.addEventListener('load', () => {
    // start polling immediately so UI reflects Mininet-driven traffic
    try { startPolling(); } catch (e) { console.error('Failed to start polling:', e); }
    const sb = document.getElementById('stopBtn');
    if (sb) sb.disabled = false;
});

function exportCharts() {
    const items = [
        {chart: unifiedChart, name: 'unified_metrics.png'},
        {chart: fChart, name: 'flows.png'},
        {chart: topPortsChart, name: 'top_ports.png'}
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
            console.log('Topology data received:', j);
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
                // prefer showing Mbps if available (more visible than tiny fractions)
                const utilLabel = (l.rate_mbps !== undefined && l.rate_mbps > 0.01)
                    ? `${l.rate_mbps.toFixed(2)} Mbps`
                    : `${(l.utilization * 100).toFixed(2)}%`;
                const titleUtil = (l.rate_mbps !== undefined && l.rate_mbps > 0.01)
                    ? `${l.rate_mbps.toFixed(3)} Mbps`
                    : `${(l.utilization * 100).toFixed(3)}%`;
                return {
                    id: l.id,
                    from: l.from,
                    to: l.to,
                    // show a clearer label: Mbps when available, otherwise percent
                    label: rer ? `REROUTED ${utilLabel}` : (l.congested ? 'CONGESTED' : utilLabel),
                    // hover tooltip with exact utilization and state
                    title: `${rer ? 'REROUTED - ' : ''}Utilization: ${titleUtil}${l.congested ? ' (CONGESTED)' : ''}`,
                    color: color,
                    width: rer ? 5 : (l.congested ? 3 : 2),
                    dashes: rer ? false : (l.congested ? true : false),
                    arrows: rer ? 'to' : '',
                    smooth: { enabled: true }
                };
            });
            topologyEdges.update(edges);
        })
        .catch(err => { 
            console.log('Topology fetch failed:', err);
            /* silently ignore until topology available */ 
        });
}

// start topology on load
window.addEventListener('load', () => {
    initTopology();
    // refresh every 2s
    setInterval(refreshTopology, 2000);
    // apply initial UI mode visuals now that chart exists
    applyModeVisuals(CURRENT_MODE);
    setChartModeVisibility(CURRENT_MODE);
});
