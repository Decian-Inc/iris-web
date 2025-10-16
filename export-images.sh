#!/bin/bash

# Decian IRIS Image Export Script
# Exports custom Docker images for distribution

echo "Exporting Decian Custom IRIS Docker Images..."
echo "============================================="

# Create export directory
mkdir -p exports
cd exports

echo "Exporting database image..."
docker save decian/iris-db:v2.4.22-custom | gzip > iris-db-custom.tar.gz

echo "Exporting application image..."
docker save decian/iris-app:v2.4.22-custom | gzip > iris-app-custom.tar.gz

echo "Exporting nginx image..."
docker save decian/iris-nginx:v2.4.22-custom | gzip > iris-nginx-custom.tar.gz

echo ""
echo "Export complete! Files created in ./exports/:"
ls -lh *.tar.gz

echo ""
echo "To import on target system:"
echo "docker load < iris-db-custom.tar.gz"
echo "docker load < iris-app-custom.tar.gz"
echo "docker load < iris-nginx-custom.tar.gz"

echo ""
echo "Total export size:"
du -sh .