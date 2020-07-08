#!/bin/bash

read -p 'GCE Project ID: ' PROJECT_ID

export PROJECT_ID=$PROJECT_ID
export DB_USERNAME=pizarra
export DB_PASSWORD=pizarra

gcloud config set project ${PROJECT_ID}
gcloud config set compute/zone europe-west4

# create DB credentials
kubectl create secret generic pizarra-credentials \
    --from-literal db_username=${DB_USERNAME} \
    --from-literal db_password=${DB_PASSWORD}

docker push eu.gcr.io/${PROJECT_ID}/pizarra
docker push eu.gcr.io/${PROJECT_ID}/nginx

gcloud container clusters create pizarra --num-nodes=2

gcloud container clusters get-credentials pizarra

# create storage in two GCE regions
kubectl apply -f storage.yaml

# deploy NFS server to share storage between PODS
kubectl apply -f nfs.yaml

# deploy Redis server
kubectl apply -f redis.yaml

# deploy DB
kubectl apply -f postgres.yaml

# deploy nginx
cat nginx.yaml.template | envsubst > nginx.yaml
kubectl apply -f nginx.yaml

# deploy Pizarra
cat pizarra.yaml.template | envsubst > pizarra.yaml
kubectl apply -f pizarra.yaml