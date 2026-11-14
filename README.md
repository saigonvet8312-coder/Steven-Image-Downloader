
# Steven Image Downloader V1

Local-first web app for searching Unsplash, Pexels and Pixabay, filtering by minimum dimensions, selecting photos and exporting a ZIP.

## Requirements
- Python 3.10+
- Node.js 20+
- API keys (free where available)

## 1. Configure API keys
Copy `backend/.env.example` to `backend/.env` and fill in keys:
- Unsplash: https://unsplash.com/developers
- Pixabay: https://pixabay.com/api/docs/
- Pexels: https://www.pexels.com/api/ (new API key issuance may be paused; the adapter is optional)

Never put API keys in frontend files or commit `.env`.

## 2. Start backend (Windows PowerShell)
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and add keys
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

## 3. Start frontend (new PowerShell window)
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## 4. Notes
- This is a local development build. Do not expose it to the public internet without authentication, rate limiting, and a security review.
- Results are filtered by actual width/height. A source may return fewer/no 4K images.
- Unsplash API requires hotlinked image URLs for display, photographer/source attribution, and a `download_location` request when a user selects a photo for use. The backend triggers that endpoint before downloading.
- Pixabay requires source attribution, 24-hour caching of API responses, and does not allow systematic mass downloads. Bulk export is limited to user-selected results; use responsibly and check the current license for each image.
- Pexels attribution is displayed. Pexels API key issuance may be temporarily paused; if you already have a key, it can be used.
- "Other websites" accepts direct HTTPS image URLs only, not webpage URLs. The backend checks public DNS/IP destinations, rejects localhost/private-network destinations and redirects. Only download content you have permission to use.
- 4K means at least 3840 pixels wide OR 2160 pixels high; it does not mean every image is 4K.

## 5. Chạy trên GitHub Codespaces (không cài gì vào máy)
1. Đưa toàn bộ thư mục này lên một repo GitHub (nên để Private). Không commit `backend/.env`.
2. (Khuyên dùng) GitHub → Settings → Codespaces → Secrets: tạo `UNSPLASH_ACCESS_KEY`, `PIXABAY_API_KEY`, (tuỳ chọn) `PEXELS_API_KEY`, cho phép repo này dùng.
3. Trên repo: **Code → Codespaces → Create codespace on main**. Đợi vài phút để tự cài đặt.
4. Khi xong, trình duyệt tự mở app ở cổng 5173. Nếu không, mở tab **PORTS** và bấm biểu tượng quả địa cầu cạnh cổng 5173.
5. Nếu điền key bằng file `backend/.env` thay vì Secrets: sửa file rồi chạy `bash start.sh` để khởi động lại.
6. Dùng xong, Codespace tự dừng sau một thời gian không hoạt động; lần sau mở lại và chạy `bash start.sh` nếu app chưa lên.
