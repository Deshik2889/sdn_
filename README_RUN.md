# Run Instructions

1) Start the system services (ONOS, modules, dashboard):

```bash
bash scripts/start_system.sh
```

2) In a separate terminal start Mininet for the topology you will use. For the 120-host test we typically run a linear topology (heavy on resources):

```bash
# Example: 120 hosts (linear topology)
sudo mn \
--topo tree,depth=4,fanout=3 \
--controller=remote,ip=127.0.0.1,port=6653 \
--switch ovs,protocols=OpenFlow13

```

Note: 120 hosts is resource intensive. Run this on a machine with sufficient CPU/RAM or use a smaller topology for demos.

3) If this is the first run, activate required ONOS apps (one-time):

```bash
ssh-keygen -f "/home/deshik/.ssh/known_hosts" -R "[127.0.0.1]:8101"
ssh -p 8101 karaf@127.0.0.1
# password (if prompted): karaf
app activate org.onosproject.openflow
app activate org.onosproject.fwd
exit
```

4) Verify ONOS sees devices:

```bash
curl -s -u onos:rocks http://127.0.0.1:8181/onos/v1/devices | jq .
```

5) Use the dashboard to run experiments:

- Open: http://127.0.0.1:5000
- Use `Baseline` / `Proposed`, then `Start Traffic` or `Congest`.

6) Generate traffic from the Mininet terminal (recommended for controlled experiments):

From the Mininet CLI (the prompt looks like `mininet>`), use host commands to start iperf servers and clients. Examples:

```bash
# Start an iperf TCP server on h1 (background)
mininet> h1 iperf -s &

# Run a TCP client from h2 to h1 for 60 seconds
mininet> h2 iperf -c 10.0.0.1 -t 60 &

# Run multiple parallel TCP clients (example: h2..h6 -> h1)
mininet> h2 iperf -c 10.0.0.1 -t 120 &
mininet> h3 iperf -c 10.0.0.1 -t 120 &
mininet> h4 iperf -c 10.0.0.1 -t 120 &

# UDP flood (use with caution) to create strong congestion on a link
mininet> h2 iperf -u -c 10.0.0.1 -b 100M -t 60 &

# Stop iperf processes from the Mininet host if needed
mininet> h1 pkill -f iperf
mininet> h2 pkill -f iperf
```

Notes:
- Replace hostnames (`h1`, `h2`, etc.) and IPs with ones from your topology (use `mininet> nodes` or `mininet> net` to inspect).
- For the 120-host topology pick a small subset of hosts to generate traffic (e.g., `h1` ← `h120`) to create targeted congestion.
- UDP traffic (`-u`) with a high bandwidth (`-b`) will saturate links faster and is useful for demonstrating congestion/reroute effects. Use it carefully on shared lab networks.
- Use background `&` so the Mininet CLI remains responsive.

7) Stop and clean up:

```bash
bash scripts/stop_system.sh
sudo mn -c
```
