#!/usr/bin/env python3
"""
Automated experiment runner

Usage: adjust MODES, REPEATS, DURATION_SECONDS, SAMPLE_INTERVAL as needed
Runs: for each mode it will set controller mode via backend, start traffic,
poll `/api/metrics` and save CSV to `results/{mode}_run{n}.csv`, then stop traffic.

Requires: dashboard backend running at http://127.0.0.1:5000
"""
import requests
import time
import csv
import os

BACKEND = "http://127.0.0.1:5000"
ONOS = "http://127.0.0.1:8181/onos/v1"
AUTH = ("onos", "rocks")

MODES = ["baseline", "proposed", "algo1", "algo2"]
REPEATS = 3
DURATION_SECONDS = 60
SAMPLE_INTERVAL = 2

os.makedirs("results", exist_ok=True)

def set_mode(mode):
    r = requests.get(f"{BACKEND}/api/mode/{mode}")
    return r.ok

def start_traffic():
    requests.get(f"{BACKEND}/api/start-traffic")

def stop_traffic():
    requests.get(f"{BACKEND}/api/stop")

def poll_metrics(outfile, duration, interval):
    end = time.time() + duration
    fieldnames = None
    with open(outfile, 'w', newline='') as csvfile:
        writer = None
        while time.time() < end:
            try:
                r = requests.get(f"{BACKEND}/api/metrics", timeout=5)
                j = r.json()
            except Exception as e:
                print('metrics poll failed:', e)
                j = {}

            # add timestamp
            j['ts'] = time.time()

            if writer is None:
                fieldnames = list(j.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            # flatten top_ports if present
            if 'top_ports' in j:
                j['top_ports'] = str(j['top_ports'])
            writer.writerow(j)
            csvfile.flush()
            time.sleep(interval)

def run():
    for mode in MODES:
        print('\n=== MODE:', mode)
        for rep in range(1, REPEATS+1):
            print(' Run', rep)
            set_mode(mode)
            time.sleep(2)
            start_traffic()
            out = f"results/{mode}_run{rep}.csv"
            poll_metrics(out, DURATION_SECONDS, SAMPLE_INTERVAL)
            stop_traffic()
            time.sleep(5)

if __name__ == '__main__':
    print('Automated runner starting')
    run()
