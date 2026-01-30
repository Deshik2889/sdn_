#!/usr/bin/env python3
"""
Generate comparison plots from CSVs saved by `automated_runner.py`.
Produces throughput, latency, packet loss overlays and bar summaries.
Outputs PNGs to `results/`.
"""
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

os.makedirs('results', exist_ok=True)

files = glob.glob('results/*_run*.csv')
if not files:
    print('No result CSVs found in results/. Run automated_runner first.')
    exit(1)

# group files by mode prefix
modes = {}
for f in files:
    basename = os.path.basename(f)
    mode = basename.split('_run')[0]
    modes.setdefault(mode, []).append(f)

def load_concat(filelist):
    dfs = []
    for f in sorted(filelist):
        df = pd.read_csv(f)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# throughput overlay
plt.figure(figsize=(8,4))
for mode, fls in modes.items():
    df = load_concat(fls)
    if 'throughput_baseline' in df.columns:
        series = df['throughput_baseline']
    elif 'throughput' in df.columns:
        series = df['throughput']
    else:
        continue
    plt.plot(series.rolling(3).mean(), label=mode)
plt.legend()
plt.title('Throughput (smoothed)')
plt.ylabel('Mbps')
plt.savefig('results/throughput_overlay.png', bbox_inches='tight')

# latency overlay
plt.figure(figsize=(8,4))
for mode, fls in modes.items():
    df = load_concat(fls)
    if 'latency_baseline' in df.columns:
        series = df['latency_baseline']
    elif 'latency' in df.columns:
        series = df['latency']
    else:
        continue
    plt.plot(series.rolling(3).mean(), label=mode)
plt.legend()
plt.title('Latency (smoothed)')
plt.ylabel('ms')
plt.savefig('results/latency_overlay.png', bbox_inches='tight')

# packet loss bar (mean)
means = {}
for mode, fls in modes.items():
    df = load_concat(fls)
    if 'packet_loss_baseline' in df.columns:
        means[mode] = df['packet_loss_baseline'].mean()
    elif 'packet_loss' in df.columns:
        means[mode] = df['packet_loss'].mean()

plt.figure(figsize=(6,4))
plt.bar(list(means.keys()), list(means.values()))
plt.title('Average Packet Loss')
plt.savefig('results/packetloss_bar.png', bbox_inches='tight')

print('Plots saved to results/')
