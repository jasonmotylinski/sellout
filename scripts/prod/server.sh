#!/usr/bin/env bash
cd /var/projects/sellout
source .venv/bin/activate
exec uvicorn main:app --uds /run/sellout.sock
