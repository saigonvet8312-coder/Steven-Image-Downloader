#!/usr/bin/env bash
# Chạy 1 lần khi tạo Codespace: cài thư viện cho backend + frontend
set -e
cd "$(dirname "$0")/.."

pip install -r backend/requirements.txt

if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
fi

cd frontend && npm install
