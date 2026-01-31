import requests
import time

# ==============================
# ONOS CONFIG
# ==============================
ONOS_IP = "http://127.0.0.1:8181"
AUTH = ("onos", "rocks")

# ==============================
# PARAMETERS
# ==============================
LINK_CAPACITY_BPS = 100_000_000  # 100 Mbps (consistent with dashboard)
MIN_TRAFFIC_BPS = 1_000_000        # 1 Mbps filter

ALPHA = 0.6                        # EWMA smoothing factor
PRED_CONGESTION_THRESHOLD = 0.75   # 75% predicted utilization

# ==============================
# STORAGE
# ==============================
previous_stats = {}
ewma_state = {}

# ==============================
# FETCH PORT STATS
# ==============================
def get_port_stats():
    url = f"{ONOS_IP}/onos/v1/statistics/ports"
    response = requests.get(url, auth=AUTH)
    return response.json()["statistics"]

# ==============================
# EWMA PREDICTION LOGIC
# ==============================
def predict_congestion():
    stats = get_port_stats()

    for device in stats:
        device_id = device["device"]

        for port in device["ports"]:
            port_no = port["port"]
            bytes_tx = port["bytesSent"]
            now = time.time()

            key = f"{device_id}:{port_no}"

            # Initialize
            if key not in previous_stats:
                previous_stats[key] = {
                    "bytes": bytes_tx,
                    "time": now,
                    "util": 0.0
                }
                ewma_state[key] = 0.0
                continue

            prev = previous_stats[key]
            delta_bytes = bytes_tx - prev["bytes"]
            delta_time = now - prev["time"]

            if delta_time <= 0:
                continue

            traffic_rate = (delta_bytes * 8) / delta_time

            if traffic_rate < MIN_TRAFFIC_BPS:
                continue

            utilization = traffic_rate / LINK_CAPACITY_BPS

            # ==============================
            # EWMA CALCULATION
            # ==============================
            ewma_prev = ewma_state.get(key, utilization)
            ewma_current = ALPHA * utilization + (1 - ALPHA) * ewma_prev
            ewma_state[key] = ewma_current

            # ==============================
            # PREDICTION STATE
            # ==============================
            if ewma_current >= PRED_CONGESTION_THRESHOLD:
                prediction = "PREDICTED_CONGESTION"
            else:
                prediction = "SAFE"

            print(
                f"[{key}] "
                f"U_now={utilization:.2f} "
                f"U_pred={ewma_current:.2f} "
                f"STATE={prediction}"
            )

            previous_stats[key] = {
                "bytes": bytes_tx,
                "time": now,
                "util": utilization
            }

# ==============================
# MAIN LOOP
# ==============================
if __name__ == "__main__":
    print("=== Module 5: EWMA Traffic Prediction Started ===")
    while True:
        predict_congestion()
        time.sleep(2)
requests
ewma_state = {}

# ==============================
# FETCH PORT STATS
# ==============================
def get_port_stats():
   url = f"{ONOS_IP}/onos/v1/statistics/ports"
   response = requests.get(url, auth=AUTH)
   return response.json()["statistics"]

# ==============================
# EWMA PREDICTION LOGIC
# ==============================
def predict_congestion():
   stats = get_port_stats()

   for device in stats:
       device_id = device["device"]

       for port in device["ports"]:
           port_no = port["port"]
           bytes_tx = port["bytesSent"]
           now = time.time()

           key = f"{device_id}:{port_no}"

           # Initialize
           if key not in previous_stats:
               previous_stats[key] = {
                   "bytes": bytes_tx,
                   "time": now,
                   "util": 0.0
               }
               ewma_state[key] = 0.0
               continue

           prev = previous_stats[key]
           delta_bytes = bytes_tx - prev["bytes"]
           delta_time = now - prev["time"]

           if delta_time <= 0:
               continue

           traffic_rate = (delta_bytes * 8) / delta_time

           if traffic_rate < MIN_TRAFFIC_BPS:
               continue

           utilization = traffic_rate / LINK_CAPACITY_BPS

           # ==============================
           # EWMA CALCULATION
           # ==============================
           ewma_prev = ewma_state.get(key, utilization)
           ewma_current = ALPHA * utilization + (1 - ALPHA) * ewma_prev
           ewma_state[key] = ewma_current

           # ==============================
           # PREDICTION STATE
           # ==============================
           if ewma_current >= PRED_CONGESTION_THRESHOLD:
               prediction = "PREDICTED_CONGESTION"
           else:
               prediction = "SAFE"

           print(
               f"[{key}] "
               f"U_now={utilization:.2f} "
               f"U_pred={ewma_current:.2f} "
               f"STATE={prediction}"
           )

           previous_stats[key] = {
               "bytes": bytes_tx,
               "time": now,
               "util": utilization
           }

# ==============================
# MAIN LOOP
# ==============================
if __name__ == "__main__":
   print("=== Module 5: EWMA Traffic Prediction Started ===")
   while True:
       predict_congestion()
       time.sleep(2)

