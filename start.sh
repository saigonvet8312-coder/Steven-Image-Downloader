#!/usr/bin/env bash
# Khởi động (hoặc khởi động lại) backend + frontend.
# Dùng lại khi bạn vừa sửa API key trong backend/.env.
cd "$(dirname "$0")"

pkill -f "uvicorn app:app" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 1

(cd backend && nohup uvicorn app:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &)
(cd frontend && nohup npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/frontend.log 2>&1 &)

sleep 3
echo "Đã chạy. Mở tab PORTS và bấm biểu tượng quả địa cầu ở cổng 5173."
echo "Xem log nếu lỗi: tail -n 30 /tmp/backend.log  hoặc  /tmp/frontend.log"
