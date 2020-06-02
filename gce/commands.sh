#!/bin/bash

export PROJECT_ID=pizarra-279100
export GCE_ZONE=europe-west4
export DB_USERNAME=pizarra
export DB_PASSWORD=pizarra

gcloud config set project ${PROJECT_ID}
gcloud config set compute/zone ${GCE_ZONE}

gcloud container clusters create pizarra --num-nodes=2

# create storage in two GCE regions
kubectl apply -f storage.yaml

# deploy NFS server to share storage between PODS
kubectl apply -f nfs.yaml

# deploy Redis server
kubectl apply -f redis.yaml

# create DB credentials
kubectl create secret generic pizarra-credentials \
    --from-literal db_username=${DB_USERNAME} \
    --from-literal db_password=${DB_PASSWORD}

# deploy DB
kubectl apply -f postgress.yaml

gcloud container clusters create pizarra-cluster --num-nodes=2