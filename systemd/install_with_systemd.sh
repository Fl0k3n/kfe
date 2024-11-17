#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

sed "s|_PROJECT_DIR_|${PROJECT_DIR}|g" "${SCRIPT_DIR}/kfeserver.service.template" > "${SCRIPT_DIR}/kfeserver.service"

sudo cp "${SCRIPT_DIR}/kfeserver.service" /etc/systemd/user/

systemctl --user enable kfeserver.service
