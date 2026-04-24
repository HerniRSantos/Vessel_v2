#!/bin/bash
# Build and run VesselControl V2 Docker

echo "Building Docker image..."
docker build -t vessel-control-v2 .

echo "Running container..."
docker run -d \
  --name vessel-v2 \
  -p 8000:8000 \
  -v $(pwd)/backend:/app/backend \
  -v $(pwd)/.env:/app/.env \
  vessel-control-v2

echo "Container started at http://localhost:8000"
echo "User: vessel"
echo "Pass: control2026"