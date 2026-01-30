import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# LOAD DATA
# ==============================
baseline = pd.read_csv("metrics/baseline.csv")
proposed = pd.read_csv("metrics/proposed.csv")

# ==============================
# THROUGHPUT GRAPH
# ==============================
plt.figure()
plt.plot(baseline["time"], baseline["throughput"], label="Baseline")
plt.plot(proposed["time"], proposed["throughput"], label="Proposed")
plt.xlabel("Time")
plt.ylabel("Throughput (Mbps)")
plt.title("Throughput Comparison")
plt.legend()
plt.savefig("../results/throughput_comparison.png")
plt.show()

# ==============================
# LATENCY GRAPH
# ==============================
plt.figure()
plt.plot(baseline["time"], baseline["latency"], label="Baseline")
plt.plot(proposed["time"], proposed["latency"], label="Proposed")
plt.xlabel("Time")
plt.ylabel("Latency (ms)")
plt.title("Latency Comparison")
plt.legend()
plt.savefig("../results/latency_comparison.png")
plt.show()

# ==============================
# PACKET LOSS GRAPH
# ==============================
plt.figure()
plt.bar(["Baseline", "Proposed"],
        [baseline["packet_loss"].mean(), proposed["packet_loss"].mean()])
plt.ylabel("Packet Loss (%)")
plt.title("Average Packet Loss Comparison")
plt.savefig("../results/packetloss_comparison.png")
plt.show()
