# Loan EMI Calculator on Kubernetes (Minikube) — DS-584 Assignment 4

Node.js/Express + jQuery/Bootstrap app that stores every calculation in a 3-member MongoDB replica set
(StatefulSet + PVCs), exposed through the NGINX Ingress controller and autoscaled with an HPA.

```
app/       Express server, static front-end, Dockerfile, .dockerignore
k8s/       namespace, mongo (headless svc, StatefulSet, init Job), ConfigMap, Deployment, Service, Ingress
k8s/hpa/   HorizontalPodAutoscaler (applied only for the autoscaling test)
scripts/   loadgen.py, profiler.py, run_experiments.py, run_hpa_test.py, plot_results.py
results/   raw CSV/JSON outputs and graphs
```

## Bring up the whole system on a fresh Minikube cluster
```powershell
minikube start --driver=docker --cpus=2 --memory=4096
minikube addons enable ingress
minikube addons enable metrics-server
minikube image build -t emi-web:1.0 ./app          # build the image inside Minikube
kubectl apply -f k8s/                              # namespace, mongo, init job, config, web, service, ingress
kubectl get pods -n emi -w                         # wait until everything is Running/Ready
kubectl logs job/mongo-init -n emi                 # shows 1 PRIMARY + 2 SECONDARY
```
Map the host name (PowerShell **as Administrator**) and keep a tunnel running in a second admin PowerShell:
```powershell
Add-Content C:\Windows\System32\drivers\etc\hosts "127.0.0.1 emi.local"
minikube tunnel
```
Open http://emi.local (on Linux with a VM driver use `$(minikube ip) emi.local` and no tunnel).

## Configuration
The app reads its MongoDB connection string only from `MONGO_URL` (ConfigMap `emi-config`).
Pod name = `HOSTNAME`, pod IP = `POD_IP` (downward API).

## API
`POST /api/emi` `{principal, rate, months}` · `GET /api/history` · `GET /health`

## Experiments
```powershell
pip install psutil pandas matplotlib
python scripts/run_experiments.py      # 5 rates x 1/2/3 replicas  -> results/fixed
python scripts/run_hpa_test.py         # 10-min HPA test           -> results/hpa_test
python scripts/plot_results.py         # graphs                    -> results/graphs
```
