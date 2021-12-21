#!/bin/bash
alembic upgrade head
cd src
python3 create_admin.py
python3 pywsgi.py

