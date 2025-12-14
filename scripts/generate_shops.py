import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = ROOT / "在地水電行.xlsx"
DATA_FILE = ROOT / "_data" / "shops.json"
PAGES_DIR = ROOT / "_pages" / "shops"

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

KEYWORDS_ADDRESS = ["路", "街", "巷", "段", "號", "村", "里"]
CATEGORY_HINTS = ["水電", "瓦斯", "五金", "工程", "材料", "公司", "行", "用品", "商店", "建築", "承辦"]
STATUS_HINTS = ["營業", "打烊", "休息", "開始營業"]


def load_rows(xlsx_path: Path):
    with zipfile.ZipFile(xlsx_path) as zf:
        with zf.open("xl/sharedStrings.xml") as f:
            shared = []
            for si in _parse_xml(f, "si"):
                text = "".join(t.text or "" for t in si.iter(f"{NS}t"))
                shared.append(text)

        rows = []
        with zf.open("xl/worksheets/sheet1.xml") as f:
            for row in _parse_xml(f, "row"):
                values = []
                for c in row.iter(f"{NS}c"):
                    cell_type = c.get("t")
                    v = c.find(f"{NS}v")
                    val = v.text if v is not None else ""
                    if cell_type == "s":
                        val = shared[int(val)]
                    values.append(val)
                rows.append(values)
    return rows


def _parse_xml(file_handle, tag):
    import xml.etree.ElementTree as ET

    tree = ET.parse(file_handle)
    return tree.getroot().iter(f"{NS}{tag}")


def is_rating(value: str) -> bool:
    try:
        score = float(value)
    except ValueError:
        return False
    return 0 < score <= 5.0


def is_review_count(value: str) -> bool:
    return re.fullmatch(r"-?\d+", value or "") is not None


def is_status(value: str) -> bool:
    return any(keyword in value for keyword in STATUS_HINTS)


def is_hours(value: str) -> bool:
    return "營業時間" in value or "開始營業" in value


def is_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value or "")
    return len(digits) >= 6 and not value.startswith("http") and not value.startswith("https")


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def is_image(value: str) -> bool:
    if not is_url(value):
        return False
    return any(domain in value for domain in ["googleusercontent", "gstatic", "streetviewpixels", "ggpht"]) or "w=122" in value


def is_address(value: str) -> bool:
    return any(token in value for token in KEYWORDS_ADDRESS) and not is_url(value) and not is_phone(value)


def is_category(value: str) -> bool:
    if is_status(value) or is_hours(value) or is_address(value) or is_url(value) or is_phone(value):
        return False
    return any(token in value for token in CATEGORY_HINTS)


def slugify(text: str, fallback: str) -> str:
    text = text.lower()
    text = re.sub(r"[\s/]+", "-", text)
    text = re.sub(r"[^a-z0-9-]", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or fallback


def parse_shops(rows):
    shops = []
    for idx, row in enumerate(rows[1:], start=1):
        if not row:
            continue
        shop = {
            "map_url": row[0].strip() if len(row) > 0 else "",
            "name": row[1].strip() if len(row) > 1 else f"Shop {idx}",
            "rating": None,
            "review_count": None,
            "category": None,
            "address": None,
            "status": None,
            "hours_note": None,
            "phone": None,
            "image_url": None,
            "review_snippet": None,
        }

        for value in row[2:]:
            value = value.strip()
            if not value:
                continue
            if shop["rating"] is None and is_rating(value):
                shop["rating"] = float(value)
                continue
            if shop["review_count"] is None and is_review_count(value):
                shop["review_count"] = abs(int(value))
                continue
            if shop["status"] is None and is_status(value):
                shop["status"] = value
                continue
            if shop["hours_note"] is None and is_hours(value):
                shop["hours_note"] = value
                continue
            if shop["phone"] is None and is_phone(value):
                shop["phone"] = value
                continue
            if shop["image_url"] is None and is_image(value):
                shop["image_url"] = value
                continue
            if shop["address"] is None and is_address(value):
                shop["address"] = value
                continue
            if shop["category"] is None and is_category(value):
                shop["category"] = value
                continue
            if shop["review_snippet"] is None and not is_url(value):
                shop["review_snippet"] = value
                continue
            if shop["image_url"] is None and is_url(value):
                shop["image_url"] = value
                continue

        slug = slugify(shop["name"], f"shop-{idx}")
        shop["slug"] = slug
        shops.append(shop)
    return shops


def write_data_file(shops):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(shops, f, ensure_ascii=False, indent=2)


def escape_quotes(text: str) -> str:
    return text.replace("\"", "\\\"")


def write_pages(shops):
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for shop in shops:
        title = escape_quotes(shop["name"])
        slug = shop["slug"]
        page_path = PAGES_DIR / f"{slug}.md"

        metadata = {
            "layout": "single",
            "title": title,
            "permalink": f"/shops/{slug}/",
            "shop": slug,
            "map_url": shop["map_url"],
            "rating": shop["rating"],
            "review_count": shop["review_count"],
            "category": shop["category"],
            "address": shop["address"],
            "status": shop["status"],
            "hours_note": shop["hours_note"],
            "phone": shop["phone"],
            "image_url": shop["image_url"],
            "review_snippet": shop["review_snippet"],
        }

        front_matter_lines = ["---"]
        for key, value in metadata.items():
            front_matter_lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        front_matter_lines.append("---\n")

        body = "\n".join(front_matter_lines) + """
{% include shop-details.md shop=page %}
"""
        page_path.write_text(body, encoding="utf-8")


def main():
    rows = load_rows(SOURCE_FILE)
    shops = parse_shops(rows)
    write_data_file(shops)
    write_pages(shops)
    print(f"Generated {len(shops)} shops")


if __name__ == "__main__":
    main()
