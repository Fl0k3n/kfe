#!/bin/bash

sudo cp kfeserver.service /etc/systemd/user/

systemctl --user enable kfeserver.service

