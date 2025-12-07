#!/bin/bash
# Wrapper script to use Windows Docker from WSL when integration is not enabled

DOCKER_EXE="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"

if [ -f "$DOCKER_EXE" ]; then
    # Use Windows Docker executable
    "$DOCKER_EXE" "$@"
else
    echo "Error: Docker Desktop not found at expected location"
    echo "Please ensure Docker Desktop is installed on Windows"
    exit 1
fi