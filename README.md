SDN Predictive Congestion Control — Quick Run
=============================================

This repository contains a demo of a predictive congestion-control system using ONOS, Mininet, and a Flask dashboard. Use the `scripts/start_system.sh` script to bring up ONOS, Mininet, monitoring modules, and the dashboard together.

Mininet 120-node command (run from terminal)
-------------------------------------------
If you want to start a ~120-host Mininet topology directly from the terminal (no helper script), run:

```bash
sudo mn --topo tree,3,4 --controller=remote,ip=127.0.0.1,port=6653 --switch ovs,protocols=OpenFlow13
```

Notes:
- The `tree,3,4` topology produces a large tree topology used for experiments (the repository's `scripts/start_system.sh` also uses this topology by default and will fall back to `tree,3,3` on low-RAM hosts).
- Make sure ONOS is running and listening on `127.0.0.1:6653` before starting Mininet (or start Mininet and then start ONOS/controller).

Recommended full startup (one command)
-------------------------------------
To start ONOS, Mininet, the monitoring modules and the dashboard together, run:

```bash
bash scripts/start_system.sh
```

After the script completes:
- Dashboard: http://127.0.0.1:5000
- ONOS UI:   http://127.0.0.1:8181/onos/ui

If this is the first ONOS run you may need to activate the OpenFlow and forwarding apps via Karaf:

```bash
# ssh -p 8101 karaf@127.0.0.1
# app activate org.onosproject.openflow
# app activate org.onosproject.fwd
```

Troubleshooting
---------------
- If Mininet or ONOS fails to start, check logs in `logs/`.
- If host memory is low, the script will fall back to `tree,3,3`.
