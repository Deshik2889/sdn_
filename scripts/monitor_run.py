#!/usr/bin/env python3
"""Monitor dashboard metrics and report congestion events.

Polls `/api/metrics` every 2s and prints throughput, state and top ports.
Detects transitions into PREDICTED_CONGESTION/CONGESTED and reports when
the system returns to SAFE for N consecutive polls (default 3) then exits.
Also checks for running iperf processes as a hint the traffic stopped.
"""
import time
import requests
import subprocess
from datetime import datetime

API = "http://127.0.0.1:5000/api/metrics"
POLL = 2.0
SAFE_CONFIRM = 3


def has_iperf_process():
    try:
        out = subprocess.check_output(["pgrep", "-f", "iperf"], stderr=subprocess.DEVNULL)
        return bool(out.strip())
    except subprocess.CalledProcessError:
        return False


def pretty(tp):
    return f"{tp:.2f} Mbps"


def main():
    last_state = None
    safe_count = 0
    print("Starting monitor; polling", API)
    while True:
        try:
            r = requests.get(API, timeout=3)
            d = r.json()
        except Exception as e:
            print(datetime.now().isoformat(), "ERROR fetching metrics:", e)
            time.sleep(POLL)
            continue

        now = datetime.now().strftime('%H:%M:%S')
        thr = d.get('throughput', 0)
        state = d.get('state', 'UNKNOWN')
        top = d.get('top_ports', [])
        tops = ", ".join([f"{p['port']}:{p.get('rate_bps',0)//1000}kb/s" for p in top[:3]]) or 'none'

        print(f"[{now}] thr={pretty(thr)} state={state} top={tops}")

        if last_state is None:
            last_state = state

        # detect transition into predicted/congested
        if state != last_state:
            print(f"--- STATE CHANGE: {last_state} -> {state} @ {now}")
            last_state = state

        # track SAFE confirmation
        if state == 'SAFE':
            safe_count += 1
        else:
            safe_count = 0

        # If SAFE has held for SAFE_CONFIRM polls and no iperf running, exit
        if safe_count >= SAFE_CONFIRM and not has_iperf_process():
            print(f"System returned to SAFE for {SAFE_CONFIRM} polls and no iperf found; assuming run completed.")
            break

        time.sleep(POLL)


if __name__ == '__main__':
    main()
