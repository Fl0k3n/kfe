#!/bin/bash

export PRELOAD_THUMBNAILS=true
export GENERATE_OPENAPI_SCHEMA_ON_STARTUP=false
export LOG_SQL=false
export DEVICE=cuda
# export DEVICE=cpu

if [ "$DEVICE" = "cuda" ]; then
    echo "Application will attempt to use GPU if it is available, if you encounter any CUDA_OUT_OF_MEMORY errors uncomment \"export DEVICE=cpu\" in the script."
    echo "To use all the features you will need at least 5GB of GPU memory. Application will work the same on cpu, but might be slower."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

source "$PROJECT_DIR/backend/env/bin/activate" && cd "$PROJECT_DIR/backend" && python -m kfe.main
