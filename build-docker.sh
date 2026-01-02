#!/bin/bash

set -e
set -u
set -o pipefail

REGISTRY="gitea.local.seward.ca"
IMAGE_NAME="vibe-dj"
REMOTE_IMAGE="$REGISTRY/mystuff/$IMAGE_NAME:latest"

trap 'echo "Logging out from $REGISTRY..."; docker logout $REGISTRY 2>/dev/null || true' EXIT

if docker login $REGISTRY --get-login 2>/dev/null | grep -q .; then
    echo "Already logged in to $REGISTRY"
else
    echo "Logging in to $REGISTRY..."
    read -p "Username: " DOCKER_USERNAME
    read -sp "Password: " DOCKER_PASSWORD
    echo
    
    echo "$DOCKER_PASSWORD" | docker login $REGISTRY --username "$DOCKER_USERNAME" --password-stdin
    
    unset DOCKER_USERNAME
    unset DOCKER_PASSWORD
fi

echo "Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

echo "Tagging image as: $REMOTE_IMAGE..."
docker tag $IMAGE_NAME $REMOTE_IMAGE

echo "Pushing image to registry..."
docker push $REMOTE_IMAGE

echo "Build and push completed successfully!"
