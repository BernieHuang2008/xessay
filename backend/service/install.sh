#!/bin/bash

# copy & chmod
cp service/xessay.service /etc/systemd/system/xessay.service
chmod 644 /etc/systemd/system/xessay.service

# reload systemd
systemctl daemon-reload

# enable auto-start
systemctl enable xessay

# run
systemctl start xessay
systemctl status xessay