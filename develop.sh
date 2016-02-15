#!/usr/bin/env bash
trap 'pkill -P $$' EXIT
set -e
./ngrok authtoken 5i6zdRYzDRPXZvv1HVKgV_2hCW7CPxeokGAD6EGeMem
~/marangx/bin/python3 -u ~/marangx_/marangx.py &
./ngrok http -subdomain=marangx localhost:8001