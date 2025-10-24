#!/bin/bash
cd /home/neurosx/DEVSPACE/fennel-deploy/fennel-service-api
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python3 manage.py runserver 0.0.0.0:8000
