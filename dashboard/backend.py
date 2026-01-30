from flask import Flask, jsonify, render_template, request
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import subprocess
import requests
import time

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================
ONOS_URL = "http://127.0.0.1:8181/onos/v1"
AUTH = ("onos", "rocks")

# ==============================
# GLOBAL STATE
# ==============================
traffic_process = None
SYSTEM_MODE = "baseline"   # baseline | proposed

ALPHA = 0.6
prev_ewma = 0.0
prev_bytes = 0
prev_time = time.time()

# store previous per-port cumulative bytes
prev_port_bytes = {}

# Reroute measurement state: when a reroute happens the rerouter will POST
# to /api/reroute and we will measure real throughput for a short window
# to report `throughput_proposed` as the measured value instead of a model.
reroute_event_time = None
measuring_reroute = False
reroute_measure_window = 6.0  # seconds to sample after a reroute
proposed_samples = []

# assumed link capacity for per-port utilization calculations (bps)
LINK_CAPACITY_BPS = 100_000_000

# ==============================
# METRICS
# ==============================
def get_live_metrics():
    global prev_ewma, prev_bytes, prev_time
    global prev_port_bytes

    r = requests.get(f"{ONOS_URL}/statistics/ports", auth=AUTH, timeout=2)
    stats = r.json().get("statistics", [])

    total_bytes = 0
    port_utilizations = {}
    for device in stats:
        device_id = device.get("device")
        for p in device.get("ports", []):
            bytes_sent = p.get("bytesSent", 0)
            total_bytes += bytes_sent

            # per-port key
            port_no = p.get("port")
            key = f"{device_id}:{port_no}"
            prev_b = prev_port_bytes.get(key, 0)
            # delta since last sample (may be zero on first call)
            delta_b = max(bytes_sent - prev_b, 0)
            # store current cumulative for next interval
            prev_port_bytes[key] = bytes_sent

            # will compute utilization after delta_time known
            port_utilizations[key] = delta_b

    # ---- REAL THROUGHPUT (RATE, NOT CUMULATIVE) ----
    now = time.time()
    delta_time = max(now - prev_time, 1)
    delta_bytes = total_bytes - prev_bytes

    throughput = (delta_bytes * 8) / (delta_time * 1e6)  # Mbps

    prev_bytes = total_bytes
    prev_time = now

    # compute per-port utilization (fraction)
    per_port_util = []
    for key, delta_b in port_utilizations.items():
        rate_bps = (delta_b * 8) / max(delta_time, 1)
        util = rate_bps / LINK_CAPACITY_BPS
        per_port_util.append((key, util, rate_bps))

    # top-5 ports by utilization
    per_port_util.sort(key=lambda x: x[1], reverse=True)
    top_ports = [ {"port": p[0], "utilization": round(p[1], 3), "rate_bps": int(p[2])} for p in per_port_util[:5] ]

    # ---- UTILIZATION ----
    # compute utilization as fraction of assumed link capacity
    utilization = min((throughput * 1e6) / LINK_CAPACITY_BPS, 1.2)

    # ---- EWMA ----
    ewma = ALPHA * utilization + (1 - ALPHA) * prev_ewma
    prev_ewma = ewma

    # expose EWMA as percent for clearer charting
    ewma_percent = ewma * 100.0

    # ---- BASELINE vs PROPOSED EFFECT ----
    # Compute both baseline and proposed metrics (for overlay comparison)
    latency_baseline = 20 + throughput * 0.4
    packet_loss_baseline = min(throughput * 0.08, 5)

    latency_proposed = 10 + throughput * 0.15
    packet_loss_proposed = min(throughput * 0.02, 2)

    # ---- STATE ----
    if ewma > 0.85:
        state = "CONGESTED"
    elif ewma > 0.65:
        state = "PREDICTED_CONGESTION"
    else:
        state = "SAFE"

    # For throughput overlay, return measured throughput for both modes.
    # Do NOT model a fixed improvement here — let the system measure real
    # changes after reroutes so the dashboard reflects actual behavior.
    throughput_baseline = throughput

    # If a reroute measurement is active, accumulate samples and compute
    # the proposed throughput from measured samples. Otherwise default to
    # the current measured throughput.
    global reroute_event_time, measuring_reroute, proposed_samples
    now_time = time.time()
    if measuring_reroute:
        # still within measurement window
        if now_time - (reroute_event_time or 0) <= reroute_measure_window:
            proposed_samples.append(throughput)
        else:
            # measurement window finished
            measuring_reroute = False
    if proposed_samples:
        # use average of samples measured after reroute
        throughput_proposed = sum(proposed_samples) / len(proposed_samples)
    else:
        throughput_proposed = throughput

    # include flows and top_ports for frontend charts
    flows = get_flow_count()

    return {
        "throughput": round(throughput, 2),
        "throughput_baseline": round(throughput_baseline, 2),
        "throughput_proposed": round(throughput_proposed, 2),
        "latency_baseline": round(latency_baseline, 2),
        "latency_proposed": round(latency_proposed, 2),
        "packet_loss_baseline": round(packet_loss_baseline, 2),
        "packet_loss_proposed": round(packet_loss_proposed, 2),
        "ewma": round(ewma, 2),
        "ewma_percent": round(ewma_percent, 2),
        "measuring_reroute": measuring_reroute,
        "proposed_samples": len(proposed_samples),
        "reroute_since": reroute_event_time,
        "state": state,
        "mode": SYSTEM_MODE,
        "flows": flows,
        "top_ports": top_ports
    }


@app.route('/api/traffic-status')
def traffic_status():
    # Return whether the backend has started a traffic process
    return jsonify({"running": traffic_process is not None})


def get_flow_count():
    try:
        r = requests.get(f"{ONOS_URL}/flows", auth=AUTH, timeout=2)
        j = r.json()
        # ONOS may return flows grouped by device or as top-level list; try common keys
        if isinstance(j, dict):
            # try multiple possible shapes
            if "flows" in j and isinstance(j["flows"], list):
                return len(j["flows"])
            # sometimes ONOS returns device->flows mapping
            total = 0
            for v in j.values():
                if isinstance(v, list):
                    total += len(v)
            if total > 0:
                return total
        if isinstance(j, list):
            return len(j)
    except Exception:
        pass
    return 0


# ==============================
# ROUTES
# ==============================
@app.route("/")
def dashboard():
    return render_template("index.html")

@app.route("/api/metrics")
def metrics():
    return jsonify(get_live_metrics())

@app.route("/api/mode/<mode>")
def set_mode(mode):
    global SYSTEM_MODE, prev_ewma, prev_bytes
    # Change system mode but preserve measurement state so charts are
    # continuous across mode switches (avoids showing artificial zeros).
    SYSTEM_MODE = mode
    return jsonify({"mode": SYSTEM_MODE})

@app.route("/api/start-traffic")
def start_traffic():
    global traffic_process
    if traffic_process is None:
        traffic_process = subprocess.Popen(
            ["bash", "-c",
             "sudo mnexec -a $(pgrep -f 'mininet:h2') iperf -c 10.0.0.1 -t 60"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    return jsonify({"status": "traffic started"})

@app.route("/api/congest")
def congest():
    subprocess.Popen(
        ["bash", "-c",
         "sudo mnexec -a $(pgrep -f 'mininet:h3') iperf -c 10.0.0.4 -u -b 900M -t 30 & \
          sudo mnexec -a $(pgrep -f 'mininet:h4') iperf -c 10.0.0.5 -u -b 900M -t 30"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return jsonify({"status": "congestion triggered"})

@app.route("/api/stop")
def stop():
    global traffic_process
    if traffic_process:
        traffic_process.terminate()
        traffic_process = None
    return jsonify({"status": "stopped"})


@app.route('/api/save-charts', methods=['POST'])
def save_charts():
    # Accept multipart/form-data files and save into repository's results/ directory
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
    os.makedirs(save_dir, exist_ok=True)

    saved = []
    for key in request.files:
        f = request.files[key]
        # ensure safe filename
        filename = secure_filename(f.filename)
        # prefix with timestamp to avoid collisions
        filename = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{filename}"
        path = os.path.join(save_dir, filename)
        f.save(path)
        saved.append(path)

    return jsonify({"saved": saved})


@app.route('/api/reroute', methods=['POST'])
def reroute_notify():
    """Called by the reroute module to notify the dashboard that a reroute
    has occurred. The dashboard will then measure throughput for a short
    window and report `throughput_proposed` as the observed value.
    """
    global reroute_event_time, measuring_reroute, proposed_samples
    try:
        # reset samples and start measuring
        proposed_samples = []
        reroute_event_time = time.time()
        measuring_reroute = True
        return jsonify({"status": "measuring", "started": reroute_event_time})
    except Exception:
        return jsonify({"status": "error"}), 500

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    print("🚀 SDN CONTROL CENTER BACKEND STARTED")
    app.run(host="0.0.0.0", port=5000, debug=True)
