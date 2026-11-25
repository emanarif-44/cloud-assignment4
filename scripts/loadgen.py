import requests, random, time, threading
from concurrent.futures import ThreadPoolExecutor

URL = "http://emi.local/api/emi"
# If your API uses different field names, change them here:
FIELD_P, FIELD_RATE, FIELD_N = "principal", "rate", "months"

local = threading.local()

def payload():
    return {FIELD_P: random.randint(10000, 1000000),
            FIELD_RATE: round(random.uniform(5, 20), 2),
            FIELD_N: random.randint(6, 120)}

def one():
    s = getattr(local, "s", None)
    if s is None:
        s = local.s = requests.Session()
    t = time.time()
    try:
        r = s.post(URL, json=payload(), timeout=10)
        ok = r.status_code == 200
    except Exception:
        ok = False
    return (time.time() - t) * 1000, ok

def run(rate, duration, pool, rate_log=None):
    start = time.time(); futs = []
    for k in range(rate * duration):
        target = start + k / rate
        while time.time() < target:
            time.sleep(0.0005)
        if rate_log is not None and k % rate == 0:
            rate_log.write(f"{time.time():.0f},{rate}\n"); rate_log.flush()
        futs.append(pool.submit(one))
    res = [f.result() for f in futs]
    lat = [l for l, ok in res if ok]
    return (sum(lat) / len(lat) if lat else 0), sum(1 for _, ok in res if not ok), len(res)

def make_pool():
    return ThreadPoolExecutor(max_workers=400)

if __name__ == "__main__":   # quick self-test: python scripts/loadgen.py
    for _ in range(5):
        r = requests.post(URL, json=payload(), timeout=10)
        print(r.status_code, r.text[:150])
