#!/bin/bash
set -e
cd ~/emi
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-mongo.yaml
kubectl rollout status statefulset/mongo -n emi --timeout=400s
kubectl delete job mongo-init -n emi --ignore-not-found
kubectl apply -f k8s/20-mongo-init-job.yaml
kubectl wait --for=condition=complete job/mongo-init -n emi --timeout=240s
echo "=== INIT JOB LOGS ==="
kubectl logs job/mongo-init -n emi
echo "=== REPLICA SET MEMBERS ==="
kubectl exec -n emi mongo-0 -- mongosh --quiet --eval 'rs.status().members.forEach(m => print(m.name, m.stateStr))'
kubectl apply -f k8s/30-configmap.yaml -f k8s/40-web.yaml
kubectl rollout status deployment/emi-web -n emi --timeout=300s
kubectl get all,pvc,configmap -n emi -o wide
