# Step-by-step guide + proof commands (save every output / screenshot for the report)

## 0. One-time setup (Windows, PowerShell)
```powershell
winget install Kubernetes.minikube
winget install Kubernetes.kubectl
```
Docker Desktop must be running (whale icon steady). Then (if it complains about memory, use --memory=3072):
```powershell
minikube start --driver=docker --cpus=2 --memory=4096
minikube addons enable ingress
minikube addons enable metrics-server
```

## Milestone 01 — app (screenshot: P=500000, rate=12, n=24 + history table)
Expected EMI = 23,536.74 / total 564,881.67 / interest 64,881.67.
Local test (needs Docker): `docker run -d -p 27017:27017 mongo:6.0`, then in `app/`:
`npm install; $env:MONGO_URL="mongodb://localhost:27017/emidb"; node server.js` -> http://localhost:3000
(You can skip local testing and take the screenshot from Minikube in Milestone 02.)

## Milestone 02 — deploy
```powershell
minikube image build -t emi-web:1.0 ./app
kubectl apply -f k8s/
kubectl get pods -n emi -w                       # Ctrl+C when all Running
kubectl logs job/mongo-init -n emi               # PROOF 1 (PRIMARY + 2 SECONDARY)
kubectl exec -n emi mongo-0 -- mongosh --quiet --eval "rs.status().members.forEach(m => print(m.name, m.stateStr))"   # PROOF 2
kubectl get all,pvc,configmap -n emi -o wide     # PROOF 3 (deliverable)
kubectl port-forward svc/emi-web 8080:80 -n emi  # open http://localhost:8080, make 3-4 calculations (screenshot)
```
Persistence test (keep a second terminal for the port-forward):
```powershell
kubectl exec -n emi mongo-0 -- mongosh --quiet emidb --eval "db.calculations.countDocuments()"   # BEFORE (use the PRIMARY pod if mongo-0 is secondary)
kubectl get pod mongo-1 -n emi -o wide ; kubectl get pvc -n emi                                   # age + PVC name BEFORE
kubectl delete pod mongo-1 -n emi
kubectl get pods -n emi -w                                                                        # same name comes back
kubectl get pod mongo-1 -n emi -o wide ; kubectl get pvc -n emi                                   # new AGE, SAME PVC (data-mongo-1)
kubectl exec -n emi mongo-0 -- mongosh --quiet emidb --eval "db.calculations.countDocuments()"   # AFTER (same count)
```
Tip: find the primary with `kubectl exec -n emi mongo-0 -- mongosh --quiet --eval "db.hello().primary"`.

## Milestone 03 — ingress, balancing, healing
```powershell
Add-Content C:\Windows\System32\drivers\etc\hosts "127.0.0.1 emi.local"     # PowerShell as Administrator
minikube tunnel                                                                 # SECOND admin PowerShell: leave it open for ALL later tests
# screenshot http://emi.local
python scripts/loadgen.py dist --url http://emi.local --n 30                    # table for 3 replicas
kubectl scale deployment emi-web --replicas=5 -n emi
kubectl get pods -n emi -w                                                      # note when new pods become Ready
python scripts/loadgen.py dist --url http://emi.local --n 30                    # table for 5 replicas
```
Self-healing (terminal A: `kubectl get pods -n emi -w`, terminal B: `python scripts/loadgen.py loop --seconds 90 --out results/heal_loop.log`):
```powershell
kubectl delete pod <one emi-web pod> -n emi                                     # web pod replaced
kubectl exec -n emi mongo-0 -- mongosh --quiet --eval "db.hello().primary"      # who is PRIMARY?
kubectl delete pod <primary pod name, e.g. mongo-0> -n emi                      # new PRIMARY is elected
kubectl exec -n emi mongo-1 -- mongosh --quiet --eval "db.hello().primary"      # new primary (try mongo-1 / mongo-2)
```
Rolling update + rollback (loop must show 0 failures):
```powershell
(Get-Content app\public\index.html) -replace 'v1.0','v1.1' | Set-Content app\public\index.html
minikube image build -t emi-web:1.1 ./app
python scripts/loadgen.py loop --seconds 120 --out results/update_loop.log      # terminal B, start first
kubectl set image deployment/emi-web emi-web=emi-web:1.1 -n emi
kubectl rollout status deployment/emi-web -n emi
kubectl rollout history deployment/emi-web -n emi
kubectl rollout undo deployment/emi-web -n emi                                  # back to 1.0
```

## Milestone 04 — load test, profiling, autoscaling
(`minikube tunnel` must still be running in its own admin PowerShell.)
```powershell
pip install psutil pandas matplotlib
kubectl top pods -n emi                           # must print numbers (wait ~1 min after metrics-server starts)
python scripts/run_experiments.py --duration 10 --pause 3 --rates 10 25     # quick dry run first (~2 min)
python scripts/run_experiments.py                 # real run: 15 runs, ~25 min -> results/fixed
python scripts/run_hpa_test.py                    # 10 min  -> results/hpa_test
kubectl get hpa emi-web -n emi -w                 # (optional) watch in another terminal, screenshot scale-up/down
python scripts/plot_results.py                    # results/graphs/graph1..3
```
If a pod count shows `<unknown>` CPU in the HPA, metrics-server isn't ready: `kubectl get pods -n kube-system`.

## Git repository
```powershell
git init ; git add . ; git commit -m "EMI calculator on Kubernetes"
git branch -M main ; git remote add origin https://github.com/<you>/emi-k8s.git ; git push -u origin main
```
