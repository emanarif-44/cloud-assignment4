import os, subprocess
from loadgen import run, make_pool
from monitor import Monitor

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "..", "results")
os.makedirs(R, exist_ok=True)
subprocess.run("kubectl scale deployment emi-web --replicas=1 -n emi", shell=True)
subprocess.run(f'kubectl apply -f "{os.path.join(HERE, "..", "k8s", "hpa.yaml")}"', shell=True)
input("Wait ~1 min until 'kubectl get hpa emi-web -n emi' shows a % number (not <unknown>), then press Enter...")
m = Monitor(os.path.join(R, "hpa_test"), hpa=True); m.start()
pool = make_pool()
with open(os.path.join(R, "hpa_test_rate.csv"), "w") as rl:
    rl.write("timestamp,rate\n")
    for rate, dur in [(10, 120), (100, 300), (10, 180)]:
        print(f"--- {rate} req/s for {dur}s ---", flush=True)
        print(run(rate, dur, pool, rl), flush=True)
m.stop()
print("ALL DONE")
