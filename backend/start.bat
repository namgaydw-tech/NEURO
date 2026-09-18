@echo off
set JWT_SECRET=dev-secret-key-for-testing-change-in-production-12345678
set ENABLE_DEMO_DATA=true
set APP_ENV=development
set HALLUCINATION_CHECK=true
set DEBUG=false
cd /d D:\stitch_neuro_ai_disease_predictor\backend
python start_server.py
