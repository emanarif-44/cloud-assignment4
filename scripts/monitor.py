import threading, time, subprocess, csv, psutil

class Monitor:
    def __init__(self, prefix, hpa=False):
        self.prefix, self.hpa, self.stop_ev, self.threads = prefix, hpa, threading.Event(), []

    def _host(self):
        with open(f"{self.prefix}_host.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["timestamp", "host_cpu_percent"])
            while not self.stop_ev.is_set():
                w.writerow([f"{time.time():.0f}", psutil.cpu_percent(interval=1)]); f.flush()

    def _pods(self):
        with open(f"{self.prefix}_pods.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["timestamp", "pod", "cpu_m", "mem_mi"])
            while not self.stop_ev.is_set():
                out = subprocess.run("kubectl top pods -n emi --no-headers", shell=True,
                                     capture_output=True, text=True).stdout
                ts = f"{time.time():.0f}"
                for line in out.strip().splitlines():
                    p = line.split()
                    if len(p) >= 3 and p[0].startswith("emi-web"):
                        w.writerow([ts, p[0], p[1].rstrip("m"), p[2].rstrip("Mi")])
                f.flush(); self.stop_ev.wait(15)

    def _hpa(self):
        with open(f"{self.prefix}_hpa.csv", "w") as f:
            f.write("timestamp,line\n")
            while not self.stop_ev.is_set():
                out = subprocess.run("kubectl get hpa emi-web -n emi --no-headers", shell=True,
                                     capture_output=True, text=True).stdout.strip()
                f.write(f"{time.time():.0f},\"{out}\"\n"); f.flush(); self.stop_ev.wait(15)

    def start(self):
        fns = [self._host, self._pods] + ([self._hpa] if self.hpa else [])
        self.threads = [threading.Thread(target=fn, daemon=True) for fn in fns]
        [t.start() for t in self.threads]

    def stop(self):
        self.stop_ev.set(); [t.join(timeout=20) for t in self.threads]
