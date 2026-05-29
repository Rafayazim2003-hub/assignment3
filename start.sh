#!/bin/bash
set -e

echo "==> Starting Minikube..."
if ! minikube status | grep -q "Running"; then
    minikube start --driver=docker
else
    echo "    Minikube already running."
fi

echo "==> Pointing Docker CLI at Minikube's daemon..."
eval $(minikube docker-env)

echo "==> Building Docker images inside Minikube..."
docker build -t flask-api:latest ./app/flask-api/
docker build -t nginx-proxy:latest ./app/nginx/

echo "==> Applying Kubernetes manifests..."

kubectl apply -f k8s/namespace.yml

kubectl apply -f k8s/mysql-secret.yml
kubectl apply -f k8s/flask-configmap.yml
kubectl apply -f k8s/nginx-configmap.yml

kubectl apply -f k8s/mysql-pv.yml
kubectl apply -f k8s/mysql-pvc.yml

kubectl apply -f k8s/mysql-deployment.yml
kubectl apply -f k8s/mysql-service.yml

kubectl apply -f k8s/flask-deployment.yml
kubectl apply -f k8s/flask-service.yml

kubectl apply -f k8s/nginx-deployment.yml
kubectl apply -f k8s/nginx-service.yml

echo "==> Waiting for deployments to become ready..."
kubectl rollout status deployment/mysql     -n assignment3 --timeout=120s
kubectl rollout status deployment/flask-api -n assignment3 --timeout=120s
kubectl rollout status deployment/nginx     -n assignment3 --timeout=60s

echo ""
echo "==> All deployments ready. Application URL:"
minikube service nginx -n assignment3 --url
