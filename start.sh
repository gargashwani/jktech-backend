#!/bin/bash

chmod +x artisan.py

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload