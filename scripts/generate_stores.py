import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT / "在地水電行.xlsx"
STORES_DIR = ROOT / "_stores"

COLUMN_MAP = {
    "A": "map_url",
    "B": "name",
    "C": "rating",
    "D": "raw_reviews",
    "E": "category",
    "F": "address",
    "G": "status",
    "H": "hours_note",
    "I": "separator",
    "J": "phone",
    "K": "image_url",
    "L": "avatar_url",
    "M": "review_intro",
    "N": "review_notice",
    "O": "badge",
    "P": "badge_separator",
    "Q": "review_part_two",
    "R": "review_part_three",
    "S": "review_part_four",
    "T": "review_part_five",
}


def load_rows():
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(XLSX_PATH) as zf:
        shared_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(t.text or "" for t in si.findall(".//main:t", ns))
            for si in shared_root.findall(".//main:si", ns)
        ]

        sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))

    rows = []
    for row in sheet.findall(".//main:row", ns):
        row_data = {}
        for cell in row.findall("main:c", ns):
            ref = cell.attrib.get("r", "")
            column = "".join(ch for ch in ref if ch.isalpha())
            value_el = cell.find("main:v", ns)
            if value_el is None:
                continue
            value = value_el.text or ""
            if cell.attrib.get("t") == "s":
                value = shared_strings[int(value)]
            row_data[column] = value
        rows.append(row_data)
    return rows


def slugify(name: str, index: int) -> str:
    normalized = unicodedata.normalize("NFKD", name).strip().lower()
    slug = re.sub(r"[^\w\-]+", "-", normalized)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or f"store-{index:02d}"


def parse_reviews(raw: str) -> int | None:
    if not raw:
        return None
    try:
        value = int(float(raw))
    except ValueError:
        return None
    return abs(value)


def build_review_text(parts: list[str]) -> str:
    cleaned = []
    for part in parts:
        if not part:
            continue
        cleaned.append(part.replace("_x000D_", " ").strip())
    combined = "".join(cleaned)
    return "" if not combined else combined.strip('"“” ')


def clean_hours(value: str) -> str:
    return value.lstrip("⋅· ").strip()


def quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
    return f'"{escaped}"'


def main():
    rows = load_rows()
    STORES_DIR.mkdir(exist_ok=True)

    for index, row in enumerate(rows[1:], start=1):
        data = {COLUMN_MAP[col]: row.get(col, "") for col in COLUMN_MAP}
        name = data.get("name", f"水電行 {index}")
        slug = slugify(name, index)
        rating = data.get("rating")
        reviews = parse_reviews(data.get("raw_reviews", ""))
        hours = clean_hours(data.get("hours_note", ""))
        review_text = build_review_text(
            [
                data.get("review_intro", ""),
                data.get("review_part_two", ""),
                data.get("review_part_three", ""),
                data.get("review_part_four", ""),
                data.get("review_part_five", ""),
            ]
        )
        summary_parts = [data.get("category", ""), data.get("address", ""), data.get("phone", "")]
        excerpt = " | ".join(part for part in summary_parts if part)

        front_matter = {
            "layout": "store",
            "title": name,
            "map_url": data.get("map_url"),
            "category": data.get("category"),
            "address": data.get("address"),
            "status": data.get("status"),
            "hours_note": hours,
            "phone": data.get("phone"),
            "image_url": data.get("image_url"),
            "avatar_url": data.get("avatar_url"),
            "rating": float(rating) if rating else None,
            "reviews_count": reviews,
            "review_snippet": review_text,
            "review_notice": data.get("review_notice"),
            "badge": data.get("badge"),
            "excerpt": excerpt,
        }

        lines = ["---"]
        for key, value in front_matter.items():
            if value in (None, "", []):
                continue
            if isinstance(value, float):
                line = f"{key}: {value:.1f}"
            elif isinstance(value, str):
                line = f"{key}: {quote(value)}"
            else:
                line = f"{key}: {value}"
            lines.append(line)
        lines.append("---")
        lines.append("\n歡迎參考店家資訊，透過下方按鈕可以在 Google 地圖查看更多細節。\n")

        (STORES_DIR / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
