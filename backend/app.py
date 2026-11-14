
import os, io, zipfile, socket, ipaddress, hashlib, time
from urllib.parse import urlparse
from typing import Optional
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image

load_dotenv()
UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "").strip()
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "").strip()

app = FastAPI(title="Steven Image Downloader API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Small in-memory cache. Pixabay requires caching API responses for 24 hours.
CACHE = {}
CACHE_TTL = 24 * 60 * 60

class SearchRequest(BaseModel):
    q: str = Field(min_length=2, max_length=100)
    page: int = Field(default=1, ge=1, le=20)
    per_page: int = Field(default=20, ge=1, le=40)
    min_width: int = Field(default=3840, ge=1, le=20000)
    min_height: int = Field(default=2160, ge=1, le=20000)
    providers: list[str] = ["unsplash", "pexels", "pixabay"]

class Photo(BaseModel):
    id: str
    provider: str
    title: str
    width: int
    height: int
    preview_url: str
    download_url: str
    page_url: str
    photographer: str = ""
    attribution: str = ""
    download_location: Optional[str] = None

class DownloadRequest(BaseModel):
    photos: list[Photo] = Field(min_length=1, max_length=20)

class AddURLRequest(BaseModel):
    url: str = Field(min_length=12, max_length=2000)
    title: str = Field(default="Website image", max_length=200)

def cache_get(key):
    item = CACHE.get(key)
    if not item:
        return None
    if time.time() - item[0] > CACHE_TTL:
        CACHE.pop(key, None)
        return None
    return item[1]

def cache_set(key, value):
    CACHE[key] = (time.time(), value)

async def get_json(url, headers=None, params=None):
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        r = await client.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json()

async def search_unsplash(q, page, per_page):
    if not UNSPLASH_KEY:
        return [], "Chưa cấu hình UNSPLASH_ACCESS_KEY"
    data = await get_json(
        "https://api.unsplash.com/search/photos",
        headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
        params={"query": q, "page": page, "per_page": per_page}
    )
    out = []
    for p in data.get("results", []):
        user = p.get("user", {})
        links = p.get("links", {})
        urls = p.get("urls", {})
        out.append(Photo(
            id=str(p["id"]), provider="unsplash",
            title=p.get("alt_description") or p.get("description") or "Unsplash photo",
            width=p.get("width", 0), height=p.get("height", 0),
            preview_url=urls.get("small") or urls.get("regular") or "",
            # Use API-returned raw URL, preserving query parameters.
            download_url=urls.get("raw") or urls.get("full") or "",
            page_url=p.get("links", {}).get("html", "https://unsplash.com"),
            photographer=user.get("name", ""),
            attribution=f"Photo by {user.get('name','Photographer')} on Unsplash",
            download_location=links.get("download_location")
        ))
    return out, None

async def search_pexels(q, page, per_page):
    if not PEXELS_KEY:
        return [], "Chưa cấu hình PEXELS_API_KEY (có thể dùng nguồn khác)"
    data = await get_json(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": q, "page": page, "per_page": min(per_page, 80), "size": "large"}
    )
    out = []
    for p in data.get("photos", []):
        src = p.get("src", {})
        photographer = p.get("photographer", "")
        out.append(Photo(
            id=str(p["id"]), provider="pexels",
            title=p.get("alt") or "Pexels photo",
            width=p.get("width", 0), height=p.get("height", 0),
            preview_url=src.get("medium") or src.get("large") or "",
            download_url=src.get("original") or src.get("large2x") or src.get("large") or "",
            page_url=p.get("url", "https://www.pexels.com"),
            photographer=photographer,
            attribution=f"Photo by {photographer} on Pexels"
        ))
    return out, None

async def search_pixabay(q, page, per_page):
    if not PIXABAY_KEY:
        return [], "Chưa cấu hình PIXABAY_API_KEY"
    data = await get_json(
        "https://pixabay.com/api/",
        params={"key": PIXABAY_KEY, "q": q, "image_type": "photo",
                "safesearch": "true", "page": page, "per_page": min(per_page, 40)}
    )
    out = []
    for p in data.get("hits", []):
        out.append(Photo(
            id=str(p["id"]), provider="pixabay",
            title=p.get("tags", "Pixabay photo"),
            width=p.get("imageWidth", 0), height=p.get("imageHeight", 0),
            preview_url=p.get("webformatURL") or p.get("previewURL") or "",
            download_url=p.get("largeImageURL") or p.get("webformatURL") or "",
            page_url=p.get("pageURL", "https://pixabay.com"),
            photographer=p.get("user", ""),
            attribution=f"Image by {p.get('user','Pixabay contributor')} from Pixabay"
        ))
    return out, None

@app.get("/api/health")
async def health():
    return {"ok": True, "configured": {
        "unsplash": bool(UNSPLASH_KEY),
        "pexels": bool(PEXELS_KEY),
        "pixabay": bool(PIXABAY_KEY)
    }}

@app.post("/api/search")
async def search(req: SearchRequest):
    q = " ".join(req.q.split())
    results, errors = [], {}
    funcs = {
        "unsplash": search_unsplash,
        "pexels": search_pexels,
        "pixabay": search_pixabay
    }
    for provider in req.providers:
        if provider not in funcs:
            continue
        cache_key = f"{provider}:{q.lower()}:{req.page}:{req.per_page}"
        cached = cache_get(cache_key)
        if cached is not None:
            items, err = cached, None
        else:
            try:
                items, err = await funcs[provider](q, req.page, req.per_page)
                if not err:
                    cache_set(cache_key, items)
            except httpx.HTTPStatusError as e:
                items, err = [], f"API trả về HTTP {e.response.status_code}"
            except Exception as e:
                items, err = [], f"Lỗi kết nối/API: {type(e).__name__}"
        if err:
            errors[provider] = err
        results.extend(items)

    # True dimension filter. Keep source metadata and do not upscale.
    results = [p for p in results if p.width >= req.min_width and p.height >= req.min_height]
    results.sort(key=lambda p: p.width * p.height, reverse=True)
    return {"query": q, "count": len(results), "results": results, "warnings": errors,
            "quality_rule": f"width >= {req.min_width} AND height >= {req.min_height}"}

def validate_public_https(url: str):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Chỉ chấp nhận URL ảnh HTTPS.")
    host = parsed.hostname.lower()
    if host in {"localhost"} or host.endswith((".local", ".internal")):
        raise ValueError("Tên miền nội bộ không được phép.")
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        ips = {ipaddress.ip_address(x[4][0]) for x in infos}
        if not ips or any(not ip.is_global for ip in ips):
            raise ValueError("URL trỏ đến mạng riêng/địa chỉ không công khai.")
    except socket.gaierror:
        raise ValueError("Không phân giải được tên miền.")
    return url

async def fetch_image(url):
    validate_public_https(url)
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        r = await client.get(url, headers={"User-Agent": "StevenImageDownloader/1.0"})
        if r.is_redirect:
            raise ValueError("Máy chủ ảnh chuyển hướng; V1 không tự đi theo redirect.")
        r.raise_for_status()
        content_type = r.headers.get("content-type", "").split(";")[0].lower()
        if not content_type.startswith("image/"):
            raise ValueError("URL không trả về dữ liệu ảnh.")
        if len(r.content) > 25 * 1024 * 1024:
            raise ValueError("Ảnh vượt giới hạn 25 MB.")
        return r.content, content_type


@app.post("/api/add-url")
async def add_direct_image(req: AddURLRequest):
    # Accept a direct HTTPS image file URL, not a webpage URL.
    try:
        content, content_type = await fetch_image(req.url)
        image = Image.open(io.BytesIO(content))
        width, height = image.size
        if width < 1 or height < 1:
            raise ValueError("Không đọc được kích thước ảnh.")
        return Photo(
            id=hashlib.sha256(req.url.encode("utf-8")).hexdigest()[:16],
            provider="website", title=req.title,
            width=width, height=height,
            preview_url=req.url, download_url=req.url,
            page_url=req.url, photographer="",
            attribution="Direct image URL supplied by user"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download-zip")
async def download_zip(req: DownloadRequest):
    mem = io.BytesIO()
    manifest = []
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, photo in enumerate(req.photos, 1):
                try:
                    if photo.provider == "unsplash":
                        # Required by Unsplash API when the user selects a photo for use.
                        if photo.download_location and UNSPLASH_KEY:
                            await client.get(photo.download_location,
                                headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"})
                    content, ctype = await fetch_image(photo.download_url)
                    ext = {"image/jpeg": ".jpg", "image/png": ".png",
                           "image/webp": ".webp", "image/gif": ".gif"}.get(ctype, ".img")
                    safe_provider = photo.provider.replace("/", "_")
                    name = f"{idx:02d}_{safe_provider}_{photo.id}{ext}"
                    zf.writestr(name, content)
                    manifest.append(f"{name}\t{photo.attribution}\t{photo.page_url}")
                except Exception as e:
                    manifest.append(f"SKIPPED\t{photo.provider}:{photo.id}\t{str(e)}")
            zf.writestr("SOURCE_AND_LICENSES.txt", "\n".join(manifest))
    mem.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(mem, media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="steven-images.zip"'})
