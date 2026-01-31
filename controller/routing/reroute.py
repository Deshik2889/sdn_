import requests
import time

# ==============================
# ONOS CONFIG
# ==============================
ONOS_URL = "http://127.0.0.1:8181/onos/v1"
AUTH = ("onos", "rocks")

# ==============================
# PARAMETERS
# ==============================
LINK_CAPACITY_BPS = 1_000_000_000
ALPHA = 0.6
PRED_THRESHOLD = 0.75
CHECK_INTERVAL = 5

# ==============================
# STATE
# ==============================
prev_stats = {}
ewma_state = {}
rerouted = False

# ==============================
# HELPERS
# ==============================
def get_port_stats():
    r = requests.get(f"{ONOS_URL}/statistics/ports", auth=AUTH)
    return r.json().get("statistics", [])

def get_devices():
    r = requests.get(f"{ONOS_URL}/devices", auth=AUTH)
    return r.json().get("devices", [])

def install_flow(device_id, in_port, out_port):
    flow = {
        "priority": 40000,
        "timeout": 0,
        "isPermanent": True,
        "deviceId": device_id,
        "treatment": {
            "instructions": [
                {"type": "OUTPUT", "port": str(out_port)}
            ]
        },
        "selector": {
            "criteria": [
                {"type": "IN_PORT", "port": str(in_port)}
            ]
        }
    }

    r = requests.post(
        f"{ONOS_URL}/flows/{device_id}",
        json=flow,
        auth=AUTH
    )

    if r.status_code in [200, 201]:
        print(f"[FLOW] Installed flow on {device_id}")
        # Notify dashboard that a reroute occurred so it can measure post-reroute throughput
        try:
            payload = {"device": device_id, "in_port": in_port, "out_port": out_port}
            requests.post("http://127.0.0.1:5000/api/reroute", json=payload, timeout=1)
        except Exception:
            pass
    else:
        print("[ERROR] Flow install failed:", r.text)

# ==============================
# MAIN LOGIC
# ==============================
def check_and_reroute():
    global rerouted
    # Query dashboard to determine current mode; if backend unreachable,
    # default to 'baseline' to avoid performing reroutes unexpectedly.
    mode = "baseline"
    try:
        resp = requests.get("http://127.0.0.1:5000/api/metrics", timeout=1)
        mode = resp.json().get("mode", "baseline")
    except Exception:
        print("[MODE] Could not reach dashboard; assuming 'baseline' mode")

    # If not in proposed mode, ensure we do not reroute and reset state
    if mode != "proposed":
        if rerouted:
            print("[MODE] Switched out of proposed mode; clearing rerouted flag")
        rerouted = False
        return

    stats = get_port_stats()
    now = time.time()

    for dev in stats:
        device_id = dev["device"]

        for p in dev["ports"]:
            key = f'{device_id}:{p["port"]}'
            bytes_tx = p["bytesSent"]

            if key not in prev_stats:
                prev_stats[key] = (bytes_tx, now)
                ewma_state[key] = 0.0
                continue

            prev_bytes, prev_time = prev_stats[key]
            dt = now - prev_time
            if dt <= 0:
                continue

            rate = (bytes_tx - prev_bytes) * 8 / dt
            util = rate / LINK_CAPACITY_BPS

            ewma = ALPHA * util + (1 - ALPHA) * ewma_state[key]
            ewma_state[key] = ewma
            prev_stats[key] = (bytes_tx, now)

            print(f"[EWMA] {key} U={util:.2f} U_pred={ewma:.2f}")

            if ewma > PRED_THRESHOLD and not rerouted:
                print("[ACTION] Predicted congestion → rerouting via flow update")

                devices = get_devices()
                if devices:
                    dpid = devices[0]["id"]
                    install_flow(dpid, 1, 2)  # example alternate port
                    rerouted = True

# ==============================
# LOOP
# ==============================
if __name__ == "__main__":
    print("=== Module 6: Predictive Flow Rerouting Started ===")

    while True:
        check_and_reroute()
        time.sleep(CHECK_INTERVAL)

