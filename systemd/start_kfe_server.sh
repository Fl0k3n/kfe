#!/bin/bash

export PRELOAD_THUMBNAILS=true
export GENERATE_OPENAPI_SCHEMA_ON_STARTUP=false
export LOG_SQL=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

source "$PROJECT_DIR/backend/env/bin/activate" && python "$PROJECT_DIR/backend/src/main.py"
