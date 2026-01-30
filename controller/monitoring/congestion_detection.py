import requests
import time

# ==============================
# ONOS CONFIGURATION
# ==============================
ONOS_IP = "http://127.0.0.1:8181"
AUTH = ("onos", "rocks")

# ==============================
# LINK & THRESHOLDS
# ==============================
LINK_CAPACITY_BPS = 1_000_000_000  # 1 Gbps
U_HIGH = 0.8        # 80% utilization
U_MID = 0.6         # 60% utilization
G_HIGH = 0.08       # growth rate threshold
MIN_TRAFFIC_BPS = 1_000_000  # 1 Mbps (filter idle ports)

# ==============================
# STORAGE FOR PREVIOUS VALUES
# ==============================
previous_stats = {}

# ==============================
# FETCH PORT STATS FROM ONOS
# ==============================
def get_port_stats():
    url = f"{ONOS_IP}/onos/v1/statistics/ports"
    response = requests.get(url, auth=AUTH)
    return response.json()["statistics"]

# ==============================
# CONGESTION DETECTION LOGIC
# ==============================
def detect_congestion():
    stats = get_port_stats()

    for device in stats:
        device_id = device["device"]

        for port in device["ports"]:
            port_no = port["port"]
            bytes_tx = port["bytesSent"]
            current_time = time.time()

            key = f"{device_id}:{port_no}"

            # First sample (initialize)
            if key not in previous_stats:
                previous_stats[key] = {
                    "bytes": bytes_tx,
                    "time": current_time,
                    "utilization": 0.0
                }
                continue

            prev = previous_stats[key]

            delta_bytes = bytes_tx - prev["bytes"]
            delta_time = current_time - prev["time"]

            if delta_time <= 0:
                continue

            # Traffic rate in bps
            traffic_rate = (delta_bytes * 8) / delta_time

            # 🔹 FILTER IDLE PORTS
            if traffic_rate < MIN_TRAFFIC_BPS:
                continue

            # Utilization
            utilization = traffic_rate / LINK_CAPACITY_BPS

            # Growth rate
            growth_rate = (utilization - prev["utilization"]) / delta_time

            # ==============================
            # STATE CLASSIFICATION
            # ==============================
            if utilization >= U_HIGH:
                state = "CONGESTED"
            elif utilization >= U_MID and growth_rate > G_HIGH:
                state = "POTENTIAL_CONGESTION"
            elif growth_rate > G_HIGH:
                state = "CONGESTED"
            else:
                state = "NORMAL"

            # ==============================
            # OUTPUT
            # ==============================
            print(
                f"[{key}] "
                f"U={utilization:.2f} "
                f"dU/dt={growth_rate:.2f} "
                f"STATE={state}"
            )

            # Update previous values
            previous_stats[key] = {
                "bytes": bytes_tx,
                "time": current_time,
                "utilization": utilization
            }

# ==============================
# MAIN LOOP
# ==============================
if __name__ == "__main__":
    print("=== Module 4: Congestion Detection Started ===")
    while True:
        detect_congestion()
        time.sleep(2)

