import os, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results") + os.sep

# Graph 1
s = pd.read_csv(R + "summary.csv")
for reps, g in s.groupby("replicas"):
    plt.plot(g["rate"], g["avg_ms"], marker="o", label=f"{reps} replica(s)")
plt.xlabel("Request rate (req/s)"); plt.ylabel("Avg response time (ms)"); plt.legend(); plt.grid()
plt.title("Graph 1: Response time vs request rate")
plt.savefig(R + "graph1.png", dpi=150); plt.clf()

# Graph 2
p = pd.read_csv(R + "r3_rate100_pods.csv"); p["t"] = p.timestamp - p.timestamp.min()
for pod, g in p.groupby("pod"):
    plt.plot(g.t, g.cpu_m, marker="o", label=pod[-5:])   # request is 100m, so millicores = % of request
plt.xlabel("Time (s)"); plt.ylabel("CPU (% of 100m request)"); plt.legend(); plt.grid()
plt.title("Graph 2: Per-pod CPU, 100 req/s, 3 replicas")
plt.savefig(R + "graph2.png", dpi=150); plt.clf()

# Graph 3
h = pd.read_csv(R + "hpa_test_hpa.csv")
h["cpu"] = h.line.str.extract(r"(\d+)%/")[0].astype(float)
h["reps"] = h.line.str.split().str[-2].astype(float)
rt = pd.read_csv(R + "hpa_test_rate.csv"); t0 = rt.timestamp.min()
fig, ax = plt.subplots(3, 1, sharex=True, figsize=(9, 8))
ax[0].step(rt.timestamp - t0, rt.rate, where="post"); ax[0].set_ylabel("Request rate (req/s)")
ax[1].plot(h.timestamp - t0, h.cpu, marker="o"); ax[1].axhline(50, ls="--", c="r"); ax[1].set_ylabel("Avg CPU %")
ax[2].step(h.timestamp - t0, h.reps, where="post"); ax[2].set_ylabel("Replicas"); ax[2].set_xlabel("Time (s)")
fig.suptitle("Graph 3: Autoscaling test")
plt.savefig(R + "graph3.png", dpi=150)
print("Graphs saved in results/")
