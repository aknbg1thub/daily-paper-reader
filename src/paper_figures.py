from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import base64
from typing import Any, Dict, List

import fitz
import requests
from PIL import Image


MIN_FIGURE_WIDTH = 240
MIN_FIGURE_HEIGHT = 180
MIN_FIGURE_AREA = 120_000
MIN_CAPTION_CROP_AREA = 30_000
WEBP_QUALITY = 82
FIGURE_META_VERSION = 7
PDFFIGURES2_JAR_ENV = "PDFFIGURES2_JAR"
PDFFIGURES2_DEFAULT_CACHE = os.path.expanduser("~/.cache/dpr-tools/pdffigures2/pdffigures2.jar")
PDFFIGURES2_REPO_CACHE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools", "pdffigures2.jar"))


def _safe_asset_key(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "paper"
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", text)
    text = text.strip("-._")
    return text or "paper"


def _relative_prefix(source_key: str, asset_key: str) -> str:
    return "/".join(["assets", "figures", source_key, _safe_asset_key(asset_key)])


def _absolute_dir(docs_dir: str, source_key: str, asset_key: str) -> str:
    return os.path.join(docs_dir, "assets", "figures", source_key, _safe_asset_key(asset_key))


def _clear_generated_figure_assets(asset_dir: str) -> None:
    if not os.path.isdir(asset_dir):
        return
    for name in os.listdir(asset_dir):
        lower = name.lower()
        if lower == "meta.json" or (
            lower.endswith(".webp")
            and (lower.startswith("fig-") or lower.startswith("caption-crop-"))
        ):
            try:
                os.remove(os.path.join(asset_dir, name))
            except OSError:
                pass


def _load_cached_figures(meta_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(meta_path):
        return []
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            payload = json.load(f) or {}
    except Exception:
        return []
    if int(payload.get("version") or 0) != FIGURE_META_VERSION:
        return []
    figures = payload.get("figures")
    if not isinstance(figures, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in figures:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        figure = {
            "url": url,
            "caption": str(item.get("caption") or "").strip(),
            "page": int(item.get("page") or 0),
            "index": int(item.get("index") or 0),
            "width": int(item.get("width") or 0),
            "height": int(item.get("height") or 0),
            "item_type": str(item.get("item_type") or item.get("type") or "figure").strip().lower() or "figure",
        }
        figure_number = str(item.get("figure_number") or "").strip()
        if figure_number:
            figure["figure_number"] = figure_number
        out.append(figure)
    return out


def _save_figures_meta(meta_path: str, figures: List[Dict[str, Any]], *, extractor: str) -> None:
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": FIGURE_META_VERSION,
                "extractor": extractor,
                "figures": figures,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def _chat_completions_url(base_url: str) -> str:
    base = str(base_url or "").strip().rstrip("/")
    if not base:
        base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _extract_json_payload(text: str) -> Any:
    raw = str(text or "").strip()
    if not raw:
        return None
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except Exception:
            return None
    return None


def _render_page_png(page: fitz.Page, scale: float = 2.0) -> tuple[bytes, int, int]:
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return pix.tobytes("png"), int(pix.width), int(pix.height)


def _call_vlm_for_page(
    *,
    page_png: bytes,
    page_width: int,
    page_height: int,
    page_no: int,
    captions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if os.getenv("DPR_DISABLE_VLM_FIGURES") == "1":
        return []
    api_key = (
        os.getenv("BLT_API_KEY")
        or os.getenv("SUMMARY_API_KEY")
        or os.getenv("LLM_API_KEY")
        or ""
    ).strip()
    if not api_key:
        return []
    base_url = (
        os.getenv("BLT_PRIMARY_BASE_URL")
        or os.getenv("SUMMARY_BASE_URL")
        or os.getenv("LLM_PRIMARY_BASE_URL")
        or os.getenv("BLT_API_BASE")
        or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    model = (
        os.getenv("DPR_FIGURE_VLM_MODEL")
        or os.getenv("SUMMARY_MODEL")
        or os.getenv("BLT_SUMMARY_MODEL")
        or "qwen3.7-max"
    ).strip()
    if not model:
        model = "qwen3.7-max"

    caption_brief = []
    for item in captions:
        rect = item.get("caption_rect")
        if not isinstance(rect, fitz.Rect):
            continue
        caption_brief.append(
            {
                "type": str(item.get("item_type") or "figure"),
                "number": str(item.get("figure_number") or ""),
                "caption": str(item.get("caption") or "")[:500],
                "caption_bbox_page_points": [
                    round(rect.x0, 1),
                    round(rect.y0, 1),
                    round(rect.x1, 1),
                    round(rect.y1, 1),
                ],
            }
        )
    if caption_brief:
        task = (
            "For each real Figure/Table caption shown in the hints, return one item with a bounding box in IMAGE PIXELS. "
            "Also include any other visible Figure/Table captions on this page that are missing from the hints. "
            "Use captions only as anchors to find the nearby visual/table body."
        )
    else:
        task = (
            "Perform an OCR-style page scan. Detect every visible Figure/Table caption on this page and return one item "
            "for each corresponding figure/table body."
        )

    prompt = (
        "You are extracting figures and tables from a scientific paper page image. "
        "Use the visible page image as the source of truth. Return strict JSON only.\n"
        f"Page image size is {page_width}x{page_height} pixels. Page number: {page_no}.\n"
        f"{task} "
        "The bbox must include only the figure/table body, excluding the caption/title text, page headers/footers, "
        "and unrelated body text. Do not crop a paragraph as a figure. Do not invent figures. "
        "Preserve the label number exactly as shown in the caption, for example 2, S2, A.1, B.1, or I. "
        "JSON schema: {\"items\":[{\"type\":\"figure|table\",\"number\":\"1\",\"bbox\":[x1,y1,x2,y2],\"caption\":\"...\"}]}.\n"
        "Caption hints:\n"
        + json.dumps(caption_brief, ensure_ascii=False)
    )
    image_b64 = base64.b64encode(page_png).decode("ascii")
    payload = {
        "model": model.replace("/think", ""),
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1800,
        "response_format": {"type": "json_object"},
    }
    if "qwen3" in model.lower():
        payload["enable_thinking"] = False
    try:
        resp = requests.post(
            _chat_completions_url(base_url),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=int(os.getenv("DPR_FIGURE_VLM_TIMEOUT", "20") or "20"),
        )
        resp.raise_for_status()
        data = resp.json()
        content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
        if isinstance(content, list):
            content = "\n".join(str(part.get("text") or part) for part in content)
        parsed = _extract_json_payload(str(content))
        items = parsed.get("items") if isinstance(parsed, dict) else None
        return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
    except Exception:
        return []


def _download_pdf_bytes(pdf_url: str, timeout: int = 90) -> bytes:
    resp = requests.get(
        str(pdf_url or "").strip(),
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=max(int(timeout or 1), 1),
    )
    resp.raise_for_status()
    return resp.content


def _resolve_pdffigures2_jar() -> str:
    candidates = [
        str(os.getenv(PDFFIGURES2_JAR_ENV) or "").strip(),
        PDFFIGURES2_DEFAULT_CACHE,
        PDFFIGURES2_REPO_CACHE,
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


def _load_image_size(path: str) -> tuple[int, int]:
    with Image.open(path) as img:
        img.load()
        return img.size


def _save_webp_from_path(src_path: str, dst_path: str) -> tuple[int, int]:
    with Image.open(src_path) as img:
        img.load()
        width, height = img.size
        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            export_img = bg
        elif img.mode != "RGB":
            export_img = img.convert("RGB")
        else:
            export_img = img.copy()
        export_img.save(dst_path, format="WEBP", quality=WEBP_QUALITY, method=6)
        return width, height


_ITEM_LABEL_RE = re.compile(
    r"\b(?P<kind>fig(?:ure)?|table|tab)\.?\s*"
    r"(?P<label>(?:[A-Z]\s*[.\-]?\s*)?\d+[A-Za-z]?|[IVXLCDM]+|S\s*\d+[A-Za-z]?)\b",
    re.IGNORECASE,
)


def _extract_figure_number(caption: str) -> str:
    item = _extract_item_label(caption)
    return item["label"] if item.get("type") == "figure" else ""


def _normalize_item_label(label: str) -> str:
    text = re.sub(r"\s+", "", str(label or "").strip())
    text = text.replace("-", ".")
    return text


def _extract_item_label(caption: str) -> Dict[str, str]:
    match = _ITEM_LABEL_RE.search(str(caption or ""))
    if not match:
        return {"type": "figure", "label": ""}
    kind = match.group("kind").lower()
    item_type = "table" if kind.startswith(("tab", "table")) else "figure"
    return {"type": item_type, "label": _normalize_item_label(match.group("label"))}


def _extract_caption_start_label(text: str) -> Dict[str, str]:
    raw = str(text or "").strip()
    match = _ITEM_LABEL_RE.match(raw)
    if not match:
        return {"type": "figure", "label": ""}
    kind = match.group("kind")
    label = _normalize_item_label(match.group("label"))
    item_type = "table" if kind.lower().startswith(("tab", "table")) else "figure"
    after = raw[match.end() :].lstrip()
    if item_type == "figure":
        if kind.lower() == "figure" and after[:1] not in {".", ":"}:
            return {"type": "figure", "label": ""}
    else:
        if kind != kind.upper() and after[:1] not in {".", ":"}:
            return {"type": "figure", "label": ""}
    return {"type": item_type, "label": label}


def _caption_sort_value(label: str) -> tuple[int, int, str]:
    text = _normalize_item_label(label)
    if not text:
        return (9, 0, "")
    roman = re.fullmatch(r"[IVXLCDM]+", text.upper())
    if roman:
        values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        total = 0
        prev = 0
        for ch in reversed(text.upper()):
            value = values.get(ch, 0)
            total = total - value if value < prev else total + value
            prev = max(prev, value)
        return (1, total, text)
    match = re.fullmatch(r"([A-Za-z]*)(?:[.]?)(\d+)([A-Za-z]?)", text)
    if match:
        prefix = match.group(1).upper()
        number = int(match.group(2))
        suffix = match.group(3).lower()
        prefix_rank = 0 if not prefix else 100 + sum(ord(ch) - 64 for ch in prefix)
        suffix_rank = ord(suffix) - 96 if suffix else 0
        return (prefix_rank, number, f"{suffix_rank:03d}")
    return (8, 0, text.lower())


def _figure_sort_key(item: Dict[str, Any]) -> tuple[int, int, int, int, str]:
    item_type = str(item.get("item_type") or "figure").lower()
    label = str(item.get("figure_number") or "").strip()
    page = int(item.get("page") or 0)
    source_index = int(item.get("_source_index") or item.get("index") or 0)
    if label:
        label_group, label_number, label_suffix = _caption_sort_value(label)
        return (
            page,
            source_index,
            label_group,
            label_number,
            label_suffix,
        )
    return (
        page,
        source_index,
        9 if item_type == "figure" else 10,
        0,
        "",
    )


def _looks_like_text_block(path: str) -> bool:
    try:
        with Image.open(path) as img:
            rgb = img.convert("RGB")
            gray = rgb.convert("L")
            width, height = gray.size
            if width <= 0 or height <= 0:
                return True
            if width * height < MIN_FIGURE_AREA:
                return True
            pixels = gray.load()
            rgb_pixels = rgb.load()
            row_dark_ratios: List[float] = []
            dark_pixels = 0
            saturation_sum = 0.0
            color_pixels = 0
            for y in range(height):
                row_dark = 0
                for x in range(width):
                    r, g, b = rgb_pixels[x, y]
                    max_channel = max(r, g, b)
                    min_channel = min(r, g, b)
                    saturation = 0.0 if max_channel <= 0 else (max_channel - min_channel) / max_channel
                    saturation_sum += saturation
                    if saturation > 0.18 and max_channel < 250:
                        color_pixels += 1
                    if pixels[x, y] < 170:
                        row_dark += 1
                dark_pixels += row_dark
                row_dark_ratios.append(row_dark / width)
    except Exception:
        return True

    total_pixels = float(width * height)
    dark_ratio = dark_pixels / total_pixels
    avg_saturation = saturation_sum / total_pixels
    color_ratio = color_pixels / total_pixels
    ink_rows = sum(1 for ratio in row_dark_ratios if ratio >= 0.015)
    line_like_rows = sum(1 for ratio in row_dark_ratios if 0.06 <= ratio <= 0.30)

    text_line_groups = 0
    in_group = False
    group_start = 0
    for idx, ratio in enumerate(row_dark_ratios):
        is_text_line = 0.015 <= ratio <= 0.45
        if is_text_line and not in_group:
            group_start = idx
            in_group = True
        elif not is_text_line and in_group:
            if idx - group_start >= 2:
                text_line_groups += 1
            in_group = False
    if in_group and height - group_start >= 2:
        text_line_groups += 1

    ink_row_ratio = ink_rows / height
    line_like_ratio = line_like_rows / height
    aspect = width / height

    # Tables are often monochrome and text-heavy. Keep them when pdffigures2
    # labels the crop as a table; only apply this rejection to unlabeled images
    # and figures.
    if avg_saturation > 0.01 or color_ratio > 0.01:
        return False
    if 0.8 <= aspect <= 2.0 and text_line_groups >= 14 and 0.09 <= dark_ratio <= 0.20 and ink_row_ratio >= 0.62 and line_like_ratio >= 0.12:
        return True
    return False


def _is_probable_text_crop(path: str, item_type: str) -> bool:
    if str(item_type or "").lower() == "table":
        return False
    return _looks_like_text_block(path)


def _disambiguate_repeated_label(
    item_type: str,
    figure_number: str,
    page: int,
    counts: Dict[tuple[str, str], int],
) -> str:
    item_type = str(item_type or "figure").strip().lower() or "figure"
    figure_number = str(figure_number or "").strip()
    if not figure_number:
        return ""
    label_key = (item_type, figure_number.lower())
    counts[label_key] = counts.get(label_key, 0) + 1
    if counts[label_key] <= 1:
        return figure_number
    page_label = f"p{int(page or 0)}"
    if re.match(r"^[A-Za-z][.\d]", figure_number):
        return f"{figure_number}-{page_label}"
    if int(page or 0) >= 8:
        return f"Appendix {figure_number}"
    return f"{figure_number}-{page_label}"


def _finalize_figure_order(figures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ordered = sorted(figures, key=_figure_sort_key)
    for index, figure in enumerate(ordered, start=1):
        figure.pop("_source_index", None)
        figure["index"] = index
    return ordered


def _label_key(item: Dict[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("item_type") or "figure").lower(),
        str(item.get("figure_number") or "").strip().lower(),
    )


def _looks_like_full_page_crop(width: int, height: int, page: fitz.Page | None) -> bool:
    if page is None:
        return False
    scale_w = float(width or 0) / float(page.rect.width or 1)
    scale_h = float(height or 0) / float(page.rect.height or 1)
    return 1.75 <= scale_w <= 2.25 and 1.75 <= scale_h <= 2.25


def _make_caption_guided_crops(
    pdf_path: str,
    output_dir: str,
    *,
    existing: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    return _merge_missing_caption_crops(pdf_path, list(existing or []), output_dir)


def _merge_candidates_by_caption(
    caption_candidates: List[Dict[str, Any]],
    fallback_candidates: List[Dict[str, Any]],
    pdf_path: str,
) -> List[Dict[str, Any]]:
    if not fallback_candidates:
        return caption_candidates

    pages: Dict[int, fitz.Page] = {}
    doc: fitz.Document | None = None
    try:
        doc = fitz.open(pdf_path)
        pages = {index + 1: doc[index] for index in range(len(doc))}
        merged: List[Dict[str, Any]] = list(caption_candidates)
        seen_labels = {_label_key(item) for item in merged if _label_key(item)[1]}
        seen_hash: set[str] = set()
        for item in merged:
            src_path = str(item.get("_source_path") or "")
            if not src_path or not os.path.exists(src_path):
                continue
            try:
                with open(src_path, "rb") as f:
                    seen_hash.add(hashlib.sha256(f.read()).hexdigest())
            except Exception:
                pass

        for item in fallback_candidates:
            label_key = _label_key(item)
            if label_key[1] and label_key in seen_labels:
                continue
            if str(item.get("item_type") or "figure").lower() == "table":
                page = pages.get(int(item.get("page") or 0))
                if _looks_like_full_page_crop(int(item.get("width") or 0), int(item.get("height") or 0), page):
                    continue
            src_path = str(item.get("_source_path") or "")
            if src_path and os.path.exists(src_path):
                try:
                    with open(src_path, "rb") as f:
                        sha = hashlib.sha256(f.read()).hexdigest()
                    if sha in seen_hash:
                        continue
                    seen_hash.add(sha)
                except Exception:
                    pass
            merged.append(item)
            if label_key[1]:
                seen_labels.add(label_key)
        return merged
    except Exception:
        return caption_candidates or fallback_candidates
    finally:
        if doc is not None:
            doc.close()


def _rect_from_region(page: fitz.Page, region: Any) -> fitz.Rect | None:
    if not isinstance(region, dict):
        return None
    page_rect = page.rect
    page_w = float(page_rect.width or 0)
    page_h = float(page_rect.height or 0)
    keys = ("x1", "y1", "x2", "y2")
    if not all(k in region for k in keys):
        return None
    try:
        x1, y1, x2, y2 = [float(region[k]) for k in keys]
    except Exception:
        return None
    # pdffigures2 regions are usually normalized. Accept absolute coordinates
    # as well so tests and future extractors can pass page units directly.
    if max(abs(x1), abs(y1), abs(x2), abs(y2)) <= 1.5:
        x1, x2 = x1 * page_w, x2 * page_w
        y1, y2 = y1 * page_h, y2 * page_h
    rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    return rect & page_rect


def _collect_caption_regions(pdf_path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return items
    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            blocks = page.get_text("blocks") or []
            for block_index, block in enumerate(blocks):
                if len(block) < 5:
                    continue
                text = str(block[4] or "").strip()
                label = _extract_caption_start_label(text)
                if not label.get("label"):
                    continue
                rect = fitz.Rect(float(block[0]), float(block[1]), float(block[2]), float(block[3]))
                items.append(
                    {
                        "item_type": label.get("type") or "figure",
                        "figure_number": label.get("label") or "",
                        "caption": re.sub(r"\s+", " ", text).strip(),
                        "page": page_index + 1,
                        "caption_rect": rect,
                        "_source_index": block_index + 1,
                    }
                )
    finally:
        doc.close()
    return items


def _union_rects(rects: List[fitz.Rect]) -> fitz.Rect | None:
    out: fitz.Rect | None = None
    for rect in rects:
        if rect.is_empty:
            continue
        out = fitz.Rect(rect) if out is None else out | rect
    return out


def _rect_area(rect: fitz.Rect) -> float:
    if hasattr(rect, "get_area"):
        return float(rect.get_area())
    return max(float(rect.width), 0.0) * max(float(rect.height), 0.0)


def _collect_visual_rects(page: fitz.Page) -> List[fitz.Rect]:
    page_rect = page.rect
    rects: List[fitz.Rect] = []
    seen: set[tuple[int, int, int, int]] = set()

    def add_rect(rect: fitz.Rect | None, *, min_area: float) -> None:
        if rect is None or rect.is_empty:
            return
        clipped = fitz.Rect(rect) & page_rect
        if clipped.is_empty or clipped.width < 4 or clipped.height < 4:
            return
        if _rect_area(clipped) < min_area:
            return
        if clipped.width > page_rect.width * 0.98 and clipped.height > page_rect.height * 0.98:
            return
        key = tuple(int(round(value)) for value in (clipped.x0, clipped.y0, clipped.x1, clipped.y1))
        if key in seen:
            return
        seen.add(key)
        rects.append(clipped)

    try:
        for image_info in page.get_images(full=True):
            xref = int(image_info[0] or 0)
            if xref <= 0:
                continue
            try:
                image_rects = page.get_image_rects(xref) or []
            except Exception:
                continue
            for rect in image_rects:
                add_rect(fitz.Rect(rect), min_area=350.0)
    except Exception:
        pass

    try:
        for drawing in page.get_drawings() or []:
            rect = drawing.get("rect") if isinstance(drawing, dict) else None
            if rect is not None:
                add_rect(fitz.Rect(rect), min_area=18.0)
            for item in drawing.get("items") or []:
                if isinstance(item, (list, tuple)) and len(item) >= 2 and item[0] == "re":
                    add_rect(fitz.Rect(item[1]), min_area=18.0)
    except Exception:
        pass

    return rects


def _caption_visual_crop_rect(
    page: fitz.Page,
    caption_rect: fitz.Rect,
    item_type: str = "figure",
) -> fitz.Rect | None:
    page_rect = page.rect
    visual_rects = _collect_visual_rects(page)
    if not visual_rects:
        return None

    horizontal_padding = max(10.0, page_rect.width * 0.018)
    vertical_padding = 8.0
    max_distance = page_rect.height * 0.58
    caption_center_x = (caption_rect.x0 + caption_rect.x1) / 2.0
    caption_is_full_width = caption_rect.width >= page_rect.width * 0.55

    def same_column(rect: fitz.Rect) -> bool:
        if caption_is_full_width:
            return True
        rect_center_x = (rect.x0 + rect.x1) / 2.0
        mid_x = page_rect.width / 2.0
        if caption_center_x < mid_x <= rect_center_x:
            return False
        if caption_center_x >= mid_x > rect_center_x:
            return False
        return True

    prefer_above = str(item_type or "figure").strip().lower() != "table"

    def collect_above() -> List[fitz.Rect]:
        return [
            rect
            for rect in visual_rects
            if rect.y1 <= caption_rect.y0 + 4.0
            and caption_rect.y0 - rect.y0 <= max_distance
            and rect.y1 >= caption_rect.y0 - max_distance
            and same_column(rect)
        ]

    def collect_below() -> List[fitz.Rect]:
        return [
            rect
            for rect in visual_rects
            if rect.y0 >= caption_rect.y1 - 4.0
            and rect.y1 - caption_rect.y1 <= max_distance
            and rect.y0 <= caption_rect.y1 + max_distance
            and same_column(rect)
        ]

    if prefer_above:
        selected = collect_above()
        caption_below = True
        if not selected:
            selected = collect_below()
            caption_below = False
    else:
        selected = collect_below()
        caption_below = False
        if not selected:
            selected = collect_above()
            caption_below = True
    if not selected:
        return None

    # Keep only the nearest vertical cluster to the caption. This avoids
    # joining unrelated figures from elsewhere on a dense two-column page.
    if caption_below:
        selected.sort(key=lambda rect: max(0.0, caption_rect.y0 - rect.y1))
    else:
        selected.sort(key=lambda rect: max(0.0, rect.y0 - caption_rect.y1))
    seed = selected[0]
    cluster = [seed]
    seed_center_x = (seed.x0 + seed.x1) / 2.0
    for rect in selected[1:]:
        rect_center_x = (rect.x0 + rect.x1) / 2.0
        same_visual_column = caption_is_full_width or abs(rect_center_x - seed_center_x) <= page_rect.width * 0.32
        overlaps_seed_band = not (rect.y0 > seed.y1 + 18.0 or rect.y1 < seed.y0 - 18.0)
        seed_contains_rect = (
            rect.x0 >= seed.x0 - 8.0
            and rect.x1 <= seed.x1 + 8.0
            and rect.y0 >= seed.y0 - 8.0
            and rect.y1 <= seed.y1 + 8.0
        )
        if same_visual_column and (overlaps_seed_band or seed_contains_rect):
            cluster.append(rect)

    union = _union_rects(cluster)
    if union is None:
        return None
    visual_area = sum(_rect_area(rect) for rect in cluster)
    if visual_area < 900.0:
        return None
    crop_source = union
    crop = fitz.Rect(
        crop_source.x0 - horizontal_padding,
        crop_source.y0 - vertical_padding,
        crop_source.x1 + horizontal_padding,
        crop_source.y1 + vertical_padding,
    ) & page_rect
    crop = _clip_rect_away_from_caption(crop, caption_rect, caption_below=caption_below)
    if crop is None:
        return None
    if crop.width < MIN_FIGURE_WIDTH / 2 or crop.height < MIN_FIGURE_HEIGHT / 2:
        return None
    return crop


def _clip_rect_away_from_caption(
    rect: fitz.Rect | None,
    caption_rect: fitz.Rect,
    *,
    caption_below: bool,
) -> fitz.Rect | None:
    if rect is None or rect.is_empty:
        return None
    gap = 4.0
    crop = fitz.Rect(rect)
    if caption_below:
        crop.y1 = min(crop.y1, caption_rect.y0 - gap)
    else:
        crop.y0 = max(crop.y0, caption_rect.y1 + gap)
    if crop.is_empty or crop.width < MIN_FIGURE_WIDTH / 3 or crop.height < MIN_FIGURE_HEIGHT / 3:
        return None
    return crop


def _caption_band_crop_rect(
    page: fitz.Page,
    caption_rect: fitz.Rect,
    item_type: str = "figure",
) -> fitz.Rect | None:
    page_rect = page.rect
    page_w = float(page_rect.width or 0)
    page_h = float(page_rect.height or 0)
    center_x = (caption_rect.x0 + caption_rect.x1) / 2.0
    margin_x = max(24.0, page_w * 0.06)

    if caption_rect.width >= page_w * 0.55 or abs(center_x - page_w / 2.0) <= page_w * 0.10:
        x0, x1 = margin_x, page_w - margin_x
    elif center_x < page_w / 2.0:
        x0, x1 = margin_x, page_w / 2.0 - 10.0
    else:
        x0, x1 = page_w / 2.0 + 10.0, page_w - margin_x

    item_type = str(item_type or "figure").strip().lower()
    if item_type == "table":
        if _caption_below_table_body(page, caption_rect):
            y0 = max(page_rect.y0 + 22.0, caption_rect.y0 - page_h * 0.26)
            y1 = caption_rect.y0 - 4.0
            caption_below = True
        else:
            y0 = caption_rect.y1 + 4.0
            y1 = min(page_rect.y1 - 22.0, caption_rect.y1 + page_h * 0.18)
            caption_below = False
    else:
        above_space = caption_rect.y0 - page_rect.y0
        below_space = page_rect.y1 - caption_rect.y1
        if above_space >= below_space * 0.55:
            y0 = max(page_rect.y0 + 22.0, caption_rect.y0 - page_h * 0.38)
            y1 = caption_rect.y0 - 4.0
            caption_below = True
        else:
            y0 = caption_rect.y1 + 4.0
            y1 = min(page_rect.y1 - 22.0, caption_rect.y1 + page_h * 0.38)
            caption_below = False
    crop = fitz.Rect(x0, y0, x1, y1) & page_rect
    return _clip_rect_away_from_caption(crop, caption_rect, caption_below=caption_below)


def _tighten_table_crop_rect(
    page: fitz.Page,
    caption_rect: fitz.Rect,
    crop_rect: fitz.Rect,
) -> fitz.Rect:
    page_rect = page.rect
    crop = fitz.Rect(crop_rect) & page_rect
    if crop.is_empty:
        return crop
    caption_below = _caption_below_table_body(page, caption_rect)

    horizontal_rules: List[fitz.Rect] = []
    try:
        for drawing in page.get_drawings() or []:
            rect = drawing.get("rect") if isinstance(drawing, dict) else None
            if rect is None:
                continue
            rule = fitz.Rect(rect)
            if rule.x1 < crop.x0 or rule.x0 > crop.x1 or rule.y1 < crop.y0 - 4.0 or rule.y0 > crop.y1 + 4.0:
                continue
            is_horizontal_rule = rule.width >= min(crop.width * 0.45, page_rect.width * 0.18) and rule.height <= 3.0
            if caption_below:
                near_caption_body = rule.y0 >= caption_rect.y0 - page_rect.height * 0.26 and rule.y0 <= caption_rect.y0 + 2.0
            else:
                near_caption_body = rule.y0 >= caption_rect.y1 - 2.0 and rule.y0 <= caption_rect.y1 + page_rect.height * 0.24
            if is_horizontal_rule and near_caption_body:
                horizontal_rules.append(rule)
    except Exception:
        horizontal_rules = []

    if horizontal_rules:
        x0 = min(rule.x0 for rule in horizontal_rules)
        x1 = max(rule.x1 for rule in horizontal_rules)
        y0 = min(rule.y0 for rule in horizontal_rules)
        y1 = max(rule.y1 for rule in horizontal_rules)
        body_y0 = max(page_rect.y0, y0 - 4.0)
        body_y1 = min(page_rect.y1, y1 + 6.0)
        if caption_below:
            body_y1 = min(body_y1, caption_rect.y0 - 2.0)
        else:
            body_y0 = max(body_y0, caption_rect.y1 + 2.0)
        tightened = fitz.Rect(
            max(page_rect.x0, x0 - 4.0),
            body_y0,
            min(page_rect.x1, x1 + 4.0),
            body_y1,
        )
        if tightened.width >= MIN_FIGURE_WIDTH / 2 and tightened.height >= MIN_FIGURE_HEIGHT / 4:
            return tightened

    body_blocks: List[fitz.Rect] = []
    try:
        for block in page.get_text("blocks") or []:
            if len(block) < 5:
                continue
            rect = fitz.Rect(float(block[0]), float(block[1]), float(block[2]), float(block[3]))
            if caption_below:
                if rect.y1 > caption_rect.y0 + 2.0:
                    continue
                if rect.y0 < caption_rect.y0 - page_rect.height * 0.26:
                    continue
            else:
                if rect.y0 < caption_rect.y1 - 2.0:
                    continue
                if rect.y0 > caption_rect.y1 + page_rect.height * 0.24:
                    continue
            overlap_x = max(0.0, min(rect.x1, crop.x1) - max(rect.x0, crop.x0))
            if overlap_x < min(rect.width, crop.width) * 0.45:
                continue
            body_blocks.append(rect)
    except Exception:
        body_blocks = []

    if body_blocks:
        body_blocks.sort(key=lambda rect: rect.y0)
        selected = [body_blocks[0]]
        for rect in body_blocks[1:]:
            if rect.y0 - selected[-1].y1 > 18.0:
                break
            selected.append(rect)
        union = _union_rects(selected)
        if union is not None:
            body_y0 = max(page_rect.y0, min(crop.y0, union.y0) - 4.0)
            body_y1 = min(page_rect.y1, union.y1 + 6.0)
            if caption_below:
                body_y0 = max(page_rect.y0, union.y0 - 4.0)
                body_y1 = min(body_y1, caption_rect.y0 - 2.0)
            else:
                body_y0 = max(body_y0, caption_rect.y1 + 2.0)
            tightened = fitz.Rect(
                max(page_rect.x0, min(crop.x0, union.x0) - 4.0),
                body_y0,
                min(page_rect.x1, max(crop.x1, union.x1) + 4.0),
                body_y1,
            )
            if tightened.width >= MIN_FIGURE_WIDTH / 2 and tightened.height >= MIN_FIGURE_HEIGHT / 4:
                return tightened

    return crop


def _vlm_bbox_to_page_rect(
    bbox: Any,
    page: fitz.Page,
    image_width: int,
    image_height: int,
) -> fitz.Rect | None:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return None
    try:
        x1, y1, x2, y2 = [float(v) for v in bbox]
    except Exception:
        return None
    if image_width <= 0 or image_height <= 0:
        return None
    page_rect = page.rect
    rect = fitz.Rect(
        min(x1, x2) / image_width * page_rect.width,
        min(y1, y2) / image_height * page_rect.height,
        max(x1, x2) / image_width * page_rect.width,
        max(y1, y2) / image_height * page_rect.height,
    ) & page_rect
    if rect.is_empty or rect.width < MIN_FIGURE_WIDTH / 3 or rect.height < MIN_FIGURE_HEIGHT / 3:
        return None
    return rect


def _normalize_vlm_detection(detected: Dict[str, Any]) -> Dict[str, str]:
    raw_type = str(detected.get("type") or "").strip().lower()
    raw_number = str(detected.get("number") or "").strip()
    caption = str(detected.get("caption") or "").strip()
    label_info = _extract_item_label(f"{raw_type or 'figure'} {raw_number}")
    if not label_info.get("label"):
        label_info = _extract_item_label(caption)
    item_type = label_info.get("type") or ("table" if raw_type.startswith(("tab", "table")) else "figure")
    number = label_info.get("label") or _normalize_item_label(raw_number)
    return {
        "item_type": "table" if str(item_type).lower().startswith(("tab", "table")) else "figure",
        "figure_number": number,
        "caption": caption,
    }


def _caption_is_below_body(page: fitz.Page, caption_rect: fitz.Rect) -> bool:
    page_rect = page.rect
    above_space = caption_rect.y0 - page_rect.y0
    below_space = page_rect.y1 - caption_rect.y1
    return caption_rect.y0 > page_rect.height * 0.35 or above_space >= below_space * 0.55


def _caption_below_table_body(page: fitz.Page, caption_rect: fitz.Rect) -> bool:
    page_rect = page.rect
    above_rules = 0
    below_rules = 0
    try:
        for drawing in page.get_drawings() or []:
            rect = drawing.get("rect") if isinstance(drawing, dict) else None
            if rect is None:
                continue
            rule = fitz.Rect(rect)
            if rule.width < page_rect.width * 0.18 or abs(rule.height) > 3.0:
                continue
            if caption_rect.y0 - page_rect.height * 0.26 <= rule.y0 <= caption_rect.y0 + 2.0:
                above_rules += 1
            if caption_rect.y1 - 2.0 <= rule.y0 <= caption_rect.y1 + page_rect.height * 0.26:
                below_rules += 1
    except Exception:
        pass
    if above_rules or below_rules:
        return above_rules >= below_rules
    return _caption_is_below_body(page, caption_rect)


def _save_page_crop(page: fitz.Page, rect: fitz.Rect, dst_path: str) -> tuple[int, int]:
    matrix = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    img.load()
    width, height = img.size
    img.save(dst_path, format="WEBP", quality=WEBP_QUALITY, method=6)
    return width, height


def _merge_missing_caption_crops(
    pdf_path: str,
    candidates: List[Dict[str, Any]],
    output_dir: str,
) -> List[Dict[str, Any]]:
    caption_items = _collect_caption_regions(pdf_path)
    seen_labels = {
        (
            str(item.get("item_type") or "figure").lower(),
            str(item.get("figure_number") or "").strip().lower(),
        )
        for item in candidates
        if str(item.get("figure_number") or "").strip()
    }
    label_counts: Dict[tuple[str, str], int] = {}
    for item in candidates:
        figure_number = str(item.get("figure_number") or "").strip()
        if figure_number:
            label_counts[(str(item.get("item_type") or "figure").lower(), figure_number.lower())] = 1
    missing = [
        item
        for item in caption_items
        if (
            str(item.get("item_type") or "figure").lower(),
            str(item.get("figure_number") or "").strip().lower(),
        )
        not in seen_labels
    ]
    if not missing and not os.getenv("DPR_FIGURE_VLM_SCAN_PAGES", "1").strip() != "0":
        return candidates

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return candidates
    try:
        by_page: Dict[int, List[Dict[str, Any]]] = {}
        for item in missing:
            by_page.setdefault(int(item.get("page") or 0), []).append(item)

        vlm_rects: Dict[tuple[str, str], fitz.Rect] = {}
        vlm_extra_items: List[Dict[str, Any]] = []
        scan_pages = os.getenv("DPR_FIGURE_VLM_SCAN_PAGES", "1").strip() != "0"
        max_scan_pages = max(int(os.getenv("DPR_FIGURE_VLM_MAX_PAGES", "40") or "40"), 0)
        pages_to_scan: List[int] = sorted(page_no for page_no in by_page if page_no > 0)
        if scan_pages and max_scan_pages:
            for page_no in range(1, len(doc) + 1):
                if page_no in by_page:
                    continue
                page = doc[page_no - 1]
                if _collect_visual_rects(page):
                    pages_to_scan.append(page_no)
                if len(pages_to_scan) >= max_scan_pages:
                    break

        for page_no in pages_to_scan[:max_scan_pages or len(pages_to_scan)]:
            if page_no <= 0 or page_no > len(doc):
                continue
            page = doc[page_no - 1]
            page_items = by_page.get(page_no, [])
            try:
                page_png, image_width, image_height = _render_page_png(page, scale=2.0)
                vlm_items = _call_vlm_for_page(
                    page_png=page_png,
                    page_width=image_width,
                    page_height=image_height,
                    page_no=page_no,
                    captions=page_items,
                )
            except Exception:
                vlm_items = []
            for detected in vlm_items:
                normalized = _normalize_vlm_detection(detected)
                item_type = normalized["item_type"]
                number = normalized["figure_number"]
                rect = _vlm_bbox_to_page_rect(detected.get("bbox"), page, image_width, image_height)
                if rect is None or not number:
                    continue
                caption_rect = None
                for hint in page_items:
                    hint_key = (
                        str(hint.get("item_type") or "figure").lower(),
                        str(hint.get("figure_number") or "").strip().lower(),
                    )
                    if hint_key == (item_type, number.lower()):
                        caption_rect = hint.get("caption_rect")
                        break
                if isinstance(caption_rect, fitz.Rect):
                    caption_below = (
                        _caption_below_table_body(page, caption_rect)
                        if item_type == "table"
                        else _caption_is_below_body(page, caption_rect)
                    )
                    clipped = _clip_rect_away_from_caption(
                        rect,
                        caption_rect,
                        caption_below=caption_below,
                    )
                    if clipped is not None:
                        rect = clipped
                    if item_type == "table":
                        rect = _tighten_table_crop_rect(page, caption_rect, rect)
                vlm_rects[(item_type, number.lower())] = rect
                if not isinstance(caption_rect, fitz.Rect):
                    vlm_extra_items.append(
                        {
                            "item_type": item_type,
                            "figure_number": number,
                            "caption": normalized["caption"],
                            "page": page_no,
                            "_crop_rect": rect,
                            "_source_index": len(vlm_extra_items) + 1,
                        }
                    )

        def append_crop_candidate(item: Dict[str, Any], crop_rect: fitz.Rect, crop_source: str) -> None:
            page_no = int(item.get("page") or 0)
            if page_no <= 0 or page_no > len(doc):
                return
            page = doc[page_no - 1]
            if crop_rect is None or crop_rect.is_empty:
                return
            if str(item.get("item_type") or "figure").lower() == "table" and isinstance(item.get("caption_rect"), fitz.Rect):
                crop_rect = _tighten_table_crop_rect(page, item["caption_rect"], crop_rect)
            if crop_rect.width < MIN_FIGURE_WIDTH / 2 or crop_rect.height < MIN_FIGURE_HEIGHT / 2:
                return
            tmp_path = os.path.join(output_dir, f"caption-crop-{len(candidates) + 1:03d}.webp")
            try:
                width, height = _save_page_crop(page, crop_rect, tmp_path)
            except Exception:
                return
            if width * height < MIN_CAPTION_CROP_AREA:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
                return
            if crop_source == "band" and _is_probable_text_crop(tmp_path, str(item.get("item_type") or "figure")):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
                return
            item = dict(item)
            item["_source_path"] = tmp_path
            item["width"] = width
            item["height"] = height
            item["_source_index"] = int(item.get("_source_index") or 0)
            item["figure_number"] = _disambiguate_repeated_label(
                str(item.get("item_type") or "figure"),
                str(item.get("figure_number") or ""),
                int(item.get("page") or 0),
                label_counts,
            )
            item.pop("caption_rect", None)
            item.pop("_crop_rect", None)
            candidates.append(item)
            seen_labels.add(
                (
                    str(item.get("item_type") or "figure").lower(),
                    str(item.get("figure_number") or "").strip().lower(),
                )
            )

        for item in missing:
            page_no = int(item.get("page") or 0)
            if page_no <= 0 or page_no > len(doc):
                continue
            page = doc[page_no - 1]
            label_key = (
                str(item.get("item_type") or "figure").lower(),
                str(item.get("figure_number") or "").strip().lower(),
            )
            crop_rect = vlm_rects.get(label_key)
            crop_source = "vlm" if crop_rect is not None else ""
            if crop_rect is None:
                crop_rect = _caption_visual_crop_rect(
                    page,
                    item["caption_rect"],
                    str(item.get("item_type") or "figure"),
                )
                if crop_rect is not None:
                    crop_source = "visual"
            if crop_rect is None:
                crop_rect = _caption_band_crop_rect(
                    page,
                    item["caption_rect"],
                    str(item.get("item_type") or "figure"),
                )
                if crop_rect is not None:
                    crop_source = "band"
            if crop_rect is None:
                continue
            append_crop_candidate(item, crop_rect, crop_source)

        for item in vlm_extra_items:
            label_key = (
                str(item.get("item_type") or "figure").lower(),
                str(item.get("figure_number") or "").strip().lower(),
            )
            if label_key[1] and label_key in seen_labels:
                continue
            append_crop_candidate(item, item["_crop_rect"], "vlm")
    finally:
        doc.close()
    return candidates


def _extract_figures_with_pdffigures2(
    pdf_path: str,
    output_dir: str,
    relative_prefix: str,
) -> List[Dict[str, Any]]:
    jar_path = _resolve_pdffigures2_jar()
    java_path = shutil.which("java")
    if not jar_path or not java_path:
        return []

    with tempfile.TemporaryDirectory(prefix="pdffigures2_") as tmp_root:
        input_dir = os.path.join(tmp_root, "input")
        data_dir = os.path.join(tmp_root, "data")
        image_dir = os.path.join(tmp_root, "images")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)

        base_name = os.path.basename(pdf_path)
        truncated = os.path.splitext(base_name)[0]
        tmp_pdf = os.path.join(input_dir, base_name)
        shutil.copy2(pdf_path, tmp_pdf)

        cmd = [
            java_path,
            "-Dsun.java2d.cmm=sun.java2d.cmm.kcms.KcmsServiceProvider",
            "-jar",
            jar_path,
            input_dir,
            "-g",
            data_dir + os.sep,
            "-m",
            image_dir + os.sep,
            "-f",
            "png",
            "-q",
        ]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return []

        json_path = os.path.join(data_dir, f"{truncated}.json")
        if not os.path.exists(json_path):
            return []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                payload = json.load(f) or {}
        except Exception:
            return []

        raw_figures = payload.get("figures") if isinstance(payload, dict) else None
        raw_tables = payload.get("tables") if isinstance(payload, dict) else None
        raw_items: List[tuple[str, Dict[str, Any]]] = []
        if isinstance(raw_figures, list):
            raw_items.extend(("figure", item) for item in raw_figures if isinstance(item, dict))
        if isinstance(raw_tables, list):
            raw_items.extend(("table", item) for item in raw_tables if isinstance(item, dict))
        if not raw_items:
            return []

        os.makedirs(output_dir, exist_ok=True)
        candidates: List[Dict[str, Any]] = []
        caption_counts: Dict[tuple[str, str], int] = {}
        seen_hash: set[str] = set()
        for source_index, (fallback_type, item) in enumerate(raw_items, start=1):
            render_url = str(item.get("renderURL") or item.get("renderUrl") or "").strip()
            if not render_url or not os.path.exists(render_url):
                continue
            try:
                width, height = _load_image_size(render_url)
            except Exception:
                continue
            page = int(item.get("page") or 0) + 1
            caption = str(item.get("caption") or "").strip()
            label_info = _extract_item_label(caption)
            item_type = label_info.get("type") or fallback_type or "figure"
            figure_number = label_info.get("label") or ""
            if width < MIN_FIGURE_WIDTH or height < MIN_FIGURE_HEIGHT or width * height < MIN_FIGURE_AREA:
                continue
            if _is_probable_text_crop(render_url, item_type):
                continue
            try:
                with open(render_url, "rb") as f:
                    sha = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                continue
            if sha in seen_hash:
                continue
            seen_hash.add(sha)

            label_key = (item_type, figure_number.lower())
            if figure_number:
                caption_counts[label_key] = caption_counts.get(label_key, 0) + 1
                if caption_counts[label_key] > 1:
                    page_label = f"p{page}"
                    if re.match(r"^[A-Za-z][.\d]", figure_number):
                        figure_number = f"{figure_number}-{page_label}"
                    elif page >= 8:
                        figure_number = f"Appendix {figure_number}"
                    else:
                        figure_number = f"{figure_number}-{page_label}"
            candidates.append(
                {
                    "_source_path": render_url,
                    "_source_index": source_index,
                    "caption": caption,
                    "page": page,
                    "item_type": item_type,
                    "figure_number": figure_number,
                    "width": width,
                    "height": height,
                }
            )

        caption_candidates = _make_caption_guided_crops(pdf_path, output_dir)
        candidates = _merge_candidates_by_caption(caption_candidates, candidates, pdf_path)

        figures: List[Dict[str, Any]] = []
        for fig_index, item in enumerate(_finalize_figure_order(candidates), start=1):
            file_name = f"fig-{fig_index:03d}.webp"
            abs_path = os.path.join(output_dir, file_name)
            src_path = str(item.pop("_source_path"))
            width, height = _save_webp_from_path(src_path, abs_path)
            if os.path.basename(src_path).startswith("caption-crop-"):
                try:
                    os.remove(src_path)
                except OSError:
                    pass
            figure = {
                "url": "/".join([relative_prefix.strip("/"), file_name]),
                "caption": str(item.get("caption") or "").strip(),
                "page": int(item.get("page") or 0),
                "index": fig_index,
                "item_type": str(item.get("item_type") or "figure").strip().lower() or "figure",
                "width": width,
                "height": height,
            }
            figure_number = str(item.get("figure_number") or "").strip()
            if figure_number:
                figure["figure_number"] = figure_number
            figures.append(figure)
        if figures:
            _save_figures_meta(os.path.join(output_dir, "meta.json"), figures, extractor="pdffigures2")
        return figures


def extract_figures_from_pdf(
    pdf_path: str,
    output_dir: str,
    relative_prefix: str,
    *,
    min_width: int = MIN_FIGURE_WIDTH,
    min_height: int = MIN_FIGURE_HEIGHT,
    min_area: int = MIN_FIGURE_AREA,
) -> List[Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    figures: List[Dict[str, Any]] = []
    seen_xref: set[int] = set()
    seen_sha: set[str] = set()
    fig_index = 1

    with fitz.open(pdf_path) as doc:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            for image_info in page.get_images(full=True):
                xref = int(image_info[0] or 0)
                if xref <= 0 or xref in seen_xref:
                    continue
                seen_xref.add(xref)
                try:
                    raw = doc.extract_image(xref)
                except Exception:
                    continue
                image_bytes = raw.get("image") if isinstance(raw, dict) else None
                if not image_bytes:
                    continue
                sha = hashlib.sha256(image_bytes).hexdigest()
                if sha in seen_sha:
                    continue
                seen_sha.add(sha)

                try:
                    with Image.open(io.BytesIO(image_bytes)) as img:
                        img.load()
                        width, height = img.size
                        if width < min_width or height < min_height or width * height < min_area:
                            continue
                        if img.mode == "RGBA":
                            bg = Image.new("RGB", img.size, (255, 255, 255))
                            bg.paste(img, mask=img.split()[-1])
                            export_img = bg
                        elif img.mode != "RGB":
                            export_img = img.convert("RGB")
                        else:
                            export_img = img.copy()
                except Exception:
                    continue

                file_name = f"fig-{fig_index:03d}.webp"
                abs_path = os.path.join(output_dir, file_name)
                export_img.save(abs_path, format="WEBP", quality=WEBP_QUALITY, method=6)

                figures.append(
                    {
                        "url": "/".join([relative_prefix.strip("/"), file_name]),
                        "caption": "",
                        "page": page_idx + 1,
                        "index": fig_index,
                        "item_type": "figure",
                        "width": width,
                        "height": height,
                    }
                )
                fig_index += 1

    caption_candidates = _make_caption_guided_crops(pdf_path, output_dir)
    if caption_candidates:
        # Caption-guided crops are closer to the paper's own Figure/Table list.
        # Prefer them over raw embedded-image extraction, which cannot know
        # labels and often duplicates or misses vector-only figures.
        figures = []
        fig_index = 1
        seen_labels: set[tuple[str, str]] = set()
        for item in caption_candidates:
            label_key = (
                str(item.get("item_type") or "figure").lower(),
                str(item.get("figure_number") or "").lower(),
            )
            if label_key in seen_labels:
                continue
            file_name = f"fig-{fig_index:03d}.webp"
            abs_path = os.path.join(output_dir, file_name)
            src_path = str(item.get("_source_path") or "")
            try:
                width, height = _save_webp_from_path(src_path, abs_path)
            except Exception:
                continue
            if os.path.basename(src_path).startswith("caption-crop-"):
                try:
                    os.remove(src_path)
                except OSError:
                    pass
            figures.append(
                {
                    "url": "/".join([relative_prefix.strip("/"), file_name]),
                    "caption": str(item.get("caption") or "").strip(),
                    "page": int(item.get("page") or 0),
                    "index": fig_index,
                    "item_type": str(item.get("item_type") or "figure").strip().lower() or "figure",
                    "width": width,
                    "height": height,
                    "figure_number": str(item.get("figure_number") or "").strip(),
                }
            )
            fig_index += 1
            seen_labels.add(label_key)

    figures = _finalize_figure_order(figures)
    _save_figures_meta(os.path.join(output_dir, "meta.json"), figures, extractor="pymupdf-images")
    return figures


def ensure_paper_figures(
    *,
    pdf_url: str,
    docs_dir: str,
    source_key: str,
    asset_key: str,
    force: bool = False,
) -> List[Dict[str, Any]]:
    if not str(pdf_url or "").strip():
        return []

    asset_dir = _absolute_dir(docs_dir, source_key, asset_key)
    relative_prefix = _relative_prefix(source_key, asset_key)
    meta_path = os.path.join(asset_dir, "meta.json")
    if not force:
        cached = _load_cached_figures(meta_path)
        if cached:
            return cached
        if os.path.exists(meta_path):
            return []
    else:
        _clear_generated_figure_assets(asset_dir)

    pdf_bytes = _download_pdf_bytes(pdf_url)
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf.write(pdf_bytes)
            tmp_pdf.flush()
            tmp_path = tmp_pdf.name
        figures = _extract_figures_with_pdffigures2(tmp_path, asset_dir, relative_prefix)
        if figures:
            return figures
        return extract_figures_from_pdf(tmp_path, asset_dir, relative_prefix)
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
