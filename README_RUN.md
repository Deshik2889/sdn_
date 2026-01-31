# Run Instructions

1) Start the system services (ONOS, modules, dashboard):

```bash
bash scripts/start_system.sh
```

2) In a separate terminal start Mininet for the topology you will use. For the 120-host test we typically run a linear topology (heavy on resources):

```bash
# Example: 120 hosts (linear topology)
sudo mn --topo linear,120 --controller=remote,ip=127.0.0.1,port=6653 --switch ovs,protocols=OpenFlow13
```

Note: 120 hosts is resource intensive. Run this on a machine with sufficient CPU/RAM or use a smaller topology for demos.

3) If this is the first run, activate required ONOS apps (one-time):

```bash
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

6) Example manual traffic from Mininet host shells:

```bash
# on a host (mininet> h1)
h1 iperf -s &
# on another host (mininet> h2)
h2 iperf -c 10.0.0.1 -t 60
```

7) Stop and clean up:

```bash
bash scripts/stop_system.sh
sudo mn -c
```
