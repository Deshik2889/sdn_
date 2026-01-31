# SDN Predictive Congestion Control — Presentation Guide

**Project Summary:**
- **Goal:** Reduce congestion by predicting hotspots and rerouting flows proactively.
- **Stack:** Mininet (emulation), ONOS (SDN controller), Flask dashboard, Chart.js + vis-network frontend, Python modules for EWMA prediction and rerouting logic.

**Quick run (for the presentation machine)**
- Open terminal 1: start system services

```bash
bash scripts/start_system.sh
```
- Open terminal 2: start Mininet (120 hosts example)

```bash
sudo mn --topo linear,120 --controller=remote,ip=127.0.0.1,port=6653 --switch ovs,protocols=OpenFlow13
```
- Open the dashboard in a browser: http://127.0.0.1:5000

**What to show (sequence — 6–8 minutes live walkthrough):**
- **1 — Setup confirmation (30s):** Point to ONOS web/CLI (optional) and the dashboard page to show the system is running.
- **2 — Baseline run (1m):** Select `Baseline`, click `Start Traffic`. Explain how baseline is measured (no predictive reroutes). Press `Congest` to trigger the congested condition and show how the dashboard marks congested links and updates charts.
- **3 — Proposed run (2m):** Switch to `Proposed`, click `Start Traffic` (or reuse running traffic), then `Congest`. Highlight:
  - Rerouted links (blue arrows / thicker lines) and labels.
  - Throughput/latency/packet-loss series: `Baseline` (dashed) vs `Proposed` (solid). Note the EWMA indicator and how it moves.
  - Explain the demo spikes: they are synthetic visualization boosts added to make differences visible during short live demos — clarify they make the effect easier to observe while the underlying algorithm is the same.
- **4 — Explain internals (1–2m):** Briefly open core files and point to:
  - `controller/monitoring/congestion_detection.py` and `controller/monitoring/ewma_prediction.py` — prediction logic and EWMA.
  - `controller/routing/reroute.py` — how reroutes are computed and applied.
  - `dashboard/backend.py` — endpoints used by the UI and demo synthesis (where demo spikes and rerouted-links are synthesized for visualization).
- **5 — Results & limitations (1m):** Show saved charts in `dashboard/metrics` or the live chart; explain measured metrics, what improved and where results are synthetic for demo clarity.

**What to click, exactly:**
- `Baseline` / `Proposed` (mode buttons) — show active styling to indicate mode.
- `Start Traffic` — starts non-blocking iperf traffic generators.
- `Congest` — triggers controlled congestion flows (and demo spikes when in Proposed mode).
- `Stop` — stops traffic and clears reroutes.
- Hover links on the topology to show tooltips (utilization, port info). Click a rerouted link to highlight.

**How to phrase the live part (avoid saying "demo" alone):**
- Use "interactive walkthrough" or "controlled demonstration". Example phrases:
  - "I'll run an interactive walkthrough of the system's behavior under congestion." 
  - "This is a controlled demonstration using light-weight synthetic spikes to make the reroute effect visible in a short time window." 
  - "For reproducibility, the dashboard also includes live metrics and saved CSVs in `dashboard/metrics`." 

Avoid weak phrasing like "this is just a demo" — instead emphasize methodology, reproducibility, and measured results.

**If examiners ask about the synthetic spikes:**
- Be transparent: say they are visualization/synthesis features added to make the difference visible during short live sessions. Then point to where the real metric collection and EWMA calculation happen, and offer to show raw CSVs or ONOS counters to validate.

**Presentation checklist (before the session):**
- Run `bash scripts/start_system.sh` and confirm ONOS is up.
- Launch Mininet with the intended topology and ensure hosts respond (pingall).
- Open the dashboard and confirm `/api/metrics` and `/api/topology` are returning values.
- Have one terminal ready with `tail -f logs/...` or `journalctl` to show logs if asked.
- Copy a short script or notes with exact button-click steps and timestamps to avoid fumbling.

**Time allocation (10–12 minute talk recommended):**
- 2 min: Motivation + problem statement
- 2 min: Architecture overview
- 4 min: Interactive walkthrough (Baseline → Proposed) with live clicks
- 2 min: Results, limitations, future work

**Will this get approved?**
- I cannot guarantee approval. Approval depends on your department's rubric and evaluation criteria (originality, implementation depth, evaluation quality, documentation).
- To maximize chances: ensure you explain the algorithm, show reproducible evidence (saved CSVs, code pointers), discuss limitations candidly, and align the presentation to your rubric (describe methodology, experiments, results, and contributions).

**Files to point the examiners to:**
- `controller/monitoring/ewma_prediction.py`
- `controller/routing/reroute.py`
- `dashboard/backend.py`
- `dashboard/static/charts.js` and `dashboard/templates/index.html`
- `dashboard/metrics/*` (saved CSVs)

**If you'd like, I can:**
- Add a short script `scripts/presentation_run.sh` to automate start + mininet + a reproducible sequence.
- Add a short slide-ready one-page summary into `README_HANDOFF.md`.

Good luck — tell me if you want the automated presentation script and I will add it.
