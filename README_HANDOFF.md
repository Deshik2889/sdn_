# SDN-Based Predictive Congestion Control — Handoff

Project: SDN-Based Predictive Congestion Control with Live Visualization (ONOS + Mininet)

Overview
- Goal: Compare Baseline (no control) vs Proposed (EWMA-based prediction + reroute) using ONOS, Mininet, iperf, and a live web dashboard.
- Live system: real traffic via `iperf`, ONOS decisions via REST/OpenFlow, and a Flask dashboard for control and visualization.

Repository layout (key files)
- `scripts/start_system.sh` — single-command startup for ONOS, Mininet, monitoring modules, and dashboard.
- `controller/monitoring/congestion_detection.py` — reads ONOS port stats; detects high utilization.
- `controller/monitoring/ewma_prediction.py` — EWMA traffic predictor; emits predicted congestion state.
- `controller/routing/reroute.py` — installs OpenFlow rules through ONOS REST API to reroute flows.
- `dashboard/backend.py` — Flask backend exposing `/api/metrics`, `/api/start-traffic`, `/api/congest`, `/api/stop`, `/api/baseline`, `/api/proposed`.
- `dashboard/templates/index.html` and `dashboard/static/` — frontend UI, charts, and controls.

What works (short)
- ONOS + Mininet integration (OpenFlow 1.3).
- Traffic generation from UI (mnexec + iperf).
- EWMA prediction and reroute logic running and affecting flows.
- Live dashboard with throughput/latency/loss/EWMA charts updated every 2s.
- Single-command system startup via `scripts/start_system.sh`.

Known limitations (intentional/pending)
- Baseline vs Proposed not overlaid on same chart yet.
- Latency and loss are synthetic (smoothed) but stable for demo purposes.
- No automated screenshot/PNG export of result charts.

Immediate next steps (deliverables for demo completeness)
1. Overlay Baseline vs Proposed on same chart (color-coded) in `dashboard/static/charts.js` and expose comparison data from `dashboard/backend.py`.
2. Implement PNG export of charts and an automated results export script that runs experiments and saves PNGs/CSV.
3. Add an endpoint or script to generate final comparison plots (PNG) in `results/` automatically after an experiment.
4. Prepare short report-ready plots and a voice-over/demo script for viva.

How to run (quick)
1. Start everything:
   - `bash scripts/start_system.sh`
2. Open the dashboard in a browser at the host/port the Flask app runs on (see `dashboard/backend.py`).
3. Use UI buttons: `Baseline`, `Proposed`, `Start Traffic`, `Congest`, `Stop` to run experiments.

Where to look for implementation details
- ONOS REST interactions: `controller/routing/reroute.py`.
- Metrics & prediction: `controller/monitoring/*`.
- Dashboard controls & charting: `dashboard/backend.py`, `dashboard/static/charts.js`, `dashboard/templates/index.html`.

Handoff notes for maintainer
- The system is intentionally real: iperf traffic is generated inside Mininet and ONOS handles flow rules — expect real-time behavior.
- For reproducing large-topology runs, ensure Mininet has sufficient resources (increase `ulimit`, run on a sufficiently provisioned VM).
- If ONOS container fails to start, check Docker logs and ensure required apps are activated (`org.onosproject.openflow`, `org.onosproject.fwd`).

Next action I'm ready to take (pick one)
- Implement overlay comparison chart and backend endpoint.
- Implement automated PNG export and results saver.

Contact / Context
- Created as the project handoff summary. Use this file as the starting point for Stage 4.2 and Stage 5 work.
