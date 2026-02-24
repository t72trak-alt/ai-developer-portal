#!/bin/bash
# Явно указываем интерпретатор Python и запускаем сервер
python -m uvicorn app.main:app --host 0.0.0.0 --port \ --reload
