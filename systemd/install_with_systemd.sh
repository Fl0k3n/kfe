#!/bin/bash

sudo cp kfeserver.service /etc/systemd/user/
sudo cp kfeclient.service /etc/systemd/user/

systemctl --user enable kfeserver.service
systemctl --user enable kfeclient.service

