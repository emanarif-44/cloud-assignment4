import subprocess, csv, time, os
from loadgen import run, make_pool
from monitor import Monitor

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(R, exist_ok=True)
sh = lambda c: subprocess.run(c, shell=True)
sh("kubectl delete hpa emi-web -n emi --ignore-not-found")
pool = make_pool()
with open(os.path.join(R, "summary.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["replicas", "rate", "avg_ms", "errors", "total"])
    for reps in [1, 2, 3]:
        sh(f"kubectl scale deployment emi-web --replicas={reps} -n emi")
        sh("kubectl rollout status deployment/emi-web -n emi")
        time.sleep(30)
        for rate in [10, 25, 50, 100, 200]:
            print(f"--- replicas={reps} rate={rate} (60s) ---", flush=True)
            m = Monitor(os.path.join(R, f"r{reps}_rate{rate}")); m.start()
            avg, err, tot = run(rate, 60, pool)
            m.stop()
            w.writerow([reps, rate, round(avg, 1), err, tot]); f.flush()
            print("RESULT:", reps, rate, round(avg, 1), err, tot, flush=True)
            time.sleep(30)
print("ALL DONE")
