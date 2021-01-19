#!/usr/bin/env bash
set -u   # crash on missing env variables
set -e   # stop on any error
set -x

# Secure endpoints
./oauth2-proxy --config oauth2-proxy.cfg 2>&1 | tee /var/log/oauth2-proxy/oauth2proxy.log &

# Start web server
exec uwsgi
