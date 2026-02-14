Progress update — work done since README_HANDOFF.md

Overview
- This file records incremental progress made after the initial handoff so downstream tools/maintainers can continue.

Completed changes
- Backend (`dashboard/backend.py`):
  - Compute per-port deltas and expose `rate_bps` and `rate_mbps`.
  - Fixed a scoping bug in `get_live_metrics()`.
  - Added `/api/debug_ports` endpoint returning raw ONOS payload + computed per-port rates and prev counters.
  - Synthesized rerouted links for visualization in `proposed` mode (visual only).
- Frontend (`dashboard/static/charts.js`):
  - Show top-port rates in Mbps and update topology labels accordingly.
  - Overlay baseline/proposed time-series and show EWMA axis.
  - Render reroute edges and congestion markers on topology UI; removed numbered marker labels.
- Demo tooling:
  - Added `scripts/monitor_run.py` to poll `/api/metrics` and log state transitions. Logs show intermittent huge spikes in throughput (likely counter/delta anomalies from ONOS).

Current status
- Flask dashboard running at `127.0.0.1:5000` serving `/api/metrics`, `/api/topology`, `/api/debug_ports`.
- Topology UI will display reroute visuals only when `SYSTEM_MODE == 'proposed'` (visualization only).
- Monitor logs: mostly low-Mbps values but intermittent implausible spikes; these should be addressed before demos to avoid false congestion events.

Recommended next steps
1. Implement defensive clipping/normalization in `get_live_metrics()`:
   - Ignore negative deltas.
   - Cap per-interval bytes by `LINK_CAPACITY_BPS * interval_seconds`.
   - Discard or smooth implausible spikes.
2. Optionally select rerouted links based on measured busiest links (`rate_bps`) instead of picking first-N topology links.
3. Re-run `scripts/monitor_run.py` to confirm spikes disappear and EWMA state stabilizes.

Files to inspect
- `dashboard/backend.py`
- `dashboard/static/charts.js`
- `scripts/monitor_run.py`

If you want, I can implement the clipping step now and re-run the monitor to verify — reply to continue.
