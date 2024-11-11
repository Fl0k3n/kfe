#!/bin/bash

echo "Building frontend..."
cd frontend || exit
npm build
cd ..

echo "Setting up backend environment..."
cd backend || exit

if [ ! -d "env" ]; then
    python3 -m venv env
fi

source env/bin/activate

pip install --no-deps -r requirements.txt

deactivate

HAS_DEPS=true

if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg is not installed. Application will NOT work without it. Follow instructions at: https://www.ffmpeg.org/download.html"
    HAS_DEPS=false
fi

if ! command -v ffprobe &> /dev/null; then
    echo "Warning: ffprobe is not installed. Application will NOT work without it. Follow instructions at: https://www.ffmpeg.org/download.html"
    HAS_DEPS=false
fi

echo "Installation complete. To start the application run systemd/start_kfe_server.sh. If you want application to be started automatically after boot run systemd/install_with_systemd.sh"

if [ "$HAS_DEPS" = false ]; then
	echo "Please install required programs before running the application"
fi

