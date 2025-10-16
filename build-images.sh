#!/bin/bash

# Decian IRIS Custom Image Build Script
# Builds production-ready Docker images with custom Decian features

echo "Building Decian Custom IRIS Docker Images..."
echo "============================================="

# Build the database image
echo "Building database image..."
docker build -t decian/iris-db:v2.4.22-custom docker/db/

# Build the main application image
echo "Building application image..."
docker build -t decian/iris-app:v2.4.22-custom -f docker/webApp/Dockerfile .

# Build the nginx image with required build args
echo "Building nginx image..."
docker build --build-arg NGINX_CONF_GID=1234 --build-arg NGINX_CONF_FILE=nginx.conf -t decian/iris-nginx:v2.4.22-custom docker/nginx/

echo ""
echo "Build complete! Custom images created:"
echo "- decian/iris-db:v2.4.22-custom"
echo "- decian/iris-app:v2.4.22-custom"
echo "- decian/iris-nginx:v2.4.22-custom"
echo ""
echo "To save images for distribution:"
echo "docker save decian/iris-db:v2.4.22-custom | gzip > iris-db-custom.tar.gz"
echo "docker save decian/iris-app:v2.4.22-custom | gzip > iris-app-custom.tar.gz"
echo "docker save decian/iris-nginx:v2.4.22-custom | gzip > iris-nginx-custom.tar.gz"
echo ""
echo "To push to registry (if configured):"
echo "docker push decian/iris-db:v2.4.22-custom"
echo "docker push decian/iris-app:v2.4.22-custom"
echo "docker push decian/iris-nginx:v2.4.22-custom"