"""Dịch từ khóa tiếng Việt -> tiếng Anh trước khi tìm ảnh.

1) Tra từ điển nội bộ (nhanh, không cần mạng, hiểu cả khi gõ không dấu).
2) Từ nào không có trong từ điển thì hỏi MyMemory (miễn phí, không cần key).
3) Nếu MyMemory lỗi/hết lượt thì dùng phần đã dịch được, app vẫn chạy bình thường.
Muốn thêm từ mới: thêm một dòng vào VI_EN bên dưới.
"""
import time
import unicodedata

VI_EN = {
    # bất động sản
    "bất động sản": "real estate", "nhà đất": "real estate", "đất nền": "land plot",
    "nhà phố": "townhouse", "nhà ống": "narrow townhouse", "biệt thự": "villa",
    "căn hộ": "apartment", "chung cư": "apartment building", "penthouse": "penthouse",
    "nhà ở": "house", "nhà": "house", "nhà mẫu": "show home", "nhà cấp 4": "single story house",
    "khu đô thị": "urban development", "khu dân cư": "residential area",
    "dự án": "construction project", "bàn giao": "handover keys", "hợp đồng": "contract",
    "mua nhà": "buying a house", "bán nhà": "house for sale", "cho thuê": "for rent",
    "môi giới": "real estate agent", "sổ đỏ": "property documents",
    # công trình / kiến trúc
    "tòa nhà": "building", "toà nhà": "building", "cao ốc": "skyscraper",
    "văn phòng": "office", "trung tâm thương mại": "shopping mall", "khách sạn": "hotel",
    "resort": "resort", "nhà xưởng": "factory building", "kho": "warehouse",
    "xây dựng": "construction", "công trình": "construction site", "kiến trúc": "architecture",
    "mặt tiền": "facade", "ban công": "balcony", "cầu thang": "staircase",
    "sân thượng": "rooftop terrace", "sân vườn": "garden", "hồ bơi": "swimming pool",
    "bể bơi": "swimming pool", "hàng rào": "fence", "cổng": "gate", "mái nhà": "roof",
    # nội thất
    "nội thất": "interior", "ngoại thất": "exterior", "đồ nội thất": "furniture",
    "phòng khách": "living room", "phòng ngủ": "bedroom", "phòng bếp": "kitchen",
    "nhà bếp": "kitchen", "phòng tắm": "bathroom", "nhà vệ sinh": "bathroom",
    "phòng làm việc": "home office", "phòng ăn": "dining room", "sofa": "sofa",
    "bàn": "table", "ghế": "chair", "giường": "bed", "đèn": "lamp", "cửa sổ": "window",
    "cửa": "door", "sàn nhà": "floor", "trần nhà": "ceiling", "tường": "wall",
    # tính từ
    "hiện đại": "modern", "sang trọng": "luxury", "cao cấp": "luxury", "đẹp": "beautiful",
    "cổ điển": "classic", "tối giản": "minimalist", "tân cổ điển": "neoclassical",
    "nhỏ": "small", "lớn": "large", "rộng": "spacious", "xanh": "green", "ấm cúng": "cozy",
    "sạch": "clean", "mới": "new", "cũ": "old",
    # thành phố / thiên nhiên
    "thành phố": "city", "đường phố": "street", "đường": "road", "cầu": "bridge",
    "nông thôn": "countryside", "làng": "village", "chợ": "market",
    "thiên nhiên": "nature", "núi": "mountain", "biển": "sea", "bãi biển": "beach",
    "sông": "river", "hồ": "lake", "rừng": "forest", "cây": "tree", "hoa": "flower",
    "hoàng hôn": "sunset", "bình minh": "sunrise", "bầu trời": "sky", "mây": "clouds",
    "ban đêm": "night", "ban ngày": "daytime", "mùa thu": "autumn", "mùa đông": "winter",
    "mùa xuân": "spring", "mùa hè": "summer", "mưa": "rain", "tuyết": "snow",
    # đời sống / công việc
    "gia đình": "family", "trẻ em": "children", "người": "people", "phụ nữ": "woman",
    "đàn ông": "man", "doanh nhân": "businessman", "cuộc họp": "business meeting",
    "làm việc": "working", "công việc": "work", "kinh doanh": "business", "tiền": "money",
    "đầu tư": "investment", "ngân hàng": "bank", "tài chính": "finance",
    "công nghệ": "technology", "máy tính": "computer", "điện thoại": "smartphone",
    "giáo dục": "education", "học sinh": "student", "trường học": "school",
    "sức khỏe": "health", "bệnh viện": "hospital", "thể thao": "sports",
    "du lịch": "travel", "ẩm thực": "food", "món ăn": "dish", "cà phê": "coffee",
    "xe hơi": "car", "ô tô": "car", "xe máy": "motorbike", "máy bay": "airplane",
    "động vật": "animal", "chó": "dog", "mèo": "cat", "chim": "bird",
    "nền": "background", "trừu tượng": "abstract", "việt nam": "vietnam",
    "hà nội": "hanoi", "sài gòn": "ho chi minh city", "hồ chí minh": "ho chi minh city",
    "đà nẵng": "da nang", "đà lạt": "dalat", "nha trang": "nha trang",
    "phú quốc": "phu quoc", "hạ long": "ha long bay",
}


def _strip(s: str) -> str:
    """Bỏ dấu tiếng Việt để so khớp được cả khi người dùng gõ không dấu."""
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


_EXACT = {unicodedata.normalize("NFC", k): v for k, v in VI_EN.items()}
_LOOSE = {_strip(k): v for k, v in VI_EN.items()}  # dùng khi người dùng gõ không dấu
_MAX_WORDS = max(len(k.split()) for k in _EXACT)
_CACHE = {}
_TTL = 24 * 3600


def _has_accent(s: str) -> bool:
    return any(ord(c) > 127 for c in s)


def dict_translate(q: str):
    """Trả về (chuỗi đã dịch bằng từ điển, danh sách từ chưa dịch được)."""
    orig = unicodedata.normalize("NFC", q.lower()).split()
    out, missed, i = [], [], 0
    while i < len(orig):
        for n in range(min(_MAX_WORDS, len(orig) - i), 0, -1):
            phrase = " ".join(orig[i:i + n])
            # Có dấu -> khớp đúng dấu (tránh nhầm "rồng" với "rộng");
            # không dấu -> khớp theo dạng đã bỏ dấu.
            hit = _EXACT.get(phrase) if _has_accent(phrase) else _LOOSE.get(phrase)
            if hit:
                out.append(hit)
                i += n
                break
        else:
            out.append(orig[i])
            missed.append(orig[i])
            i += 1
    return " ".join(out), missed


async def _mymemory(q: str):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=6) as client:
            r = await client.get("https://api.mymemory.translated.net/get",
                                 params={"q": q, "langpair": "vi|en"})
            d = r.json()
        text = ((d.get("responseData") or {}).get("translatedText") or "").strip()
        if str(d.get("responseStatus")) == "200" and text \
                and "MYMEMORY" not in text.upper() and not _has_accent(text):
            return text.lower()
    except Exception:
        pass
    return None


async def translate_query(q: str):
    """Trả về (từ khóa dùng để tìm, đã_dịch?)."""
    q = " ".join(q.split())
    if not q:
        return q, False
    key = q.lower()
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1], hit[1] != key

    en, missed = dict_translate(q)
    if len(missed) == len(q.split()) and not _has_accent(q):
        result = q  # câu tiếng Anh thuần, giữ nguyên
    elif any(_has_accent(w) for w in missed):
        result = await _mymemory(q) or en
    else:
        result = en

    _CACHE[key] = (time.time(), result)
    return result, result != key
