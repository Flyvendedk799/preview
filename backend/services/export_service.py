"""
Export service for MyMetaView 4.0 P7 — PNG, PDF, ZIP, embed code generation.
"""
import io
import zipfile
import logging
from typing import List, Optional, Tuple
import requests
from PIL import Image

logger = logging.getLogger(__name__)

# img2pdf for PDF generation
try:
    import img2pdf
    HAS_IMG2PDF = True
except ImportError:
    HAS_IMG2PDF = False


def _fetch_image(url: str, timeout: int = 30) -> bytes:
    """Fetch image bytes from URL. Raises on failure."""
    resp = requests.get(url, timeout=timeout, stream=True)
    resp.raise_for_status()
    return resp.content


def export_as_png(preview_image_url: str) -> Tuple[bytes, str]:
    """
    Fetch preview image and return as PNG bytes with filename.
    If source is already PNG, returns as-is; otherwise converts.
    """
    data = _fetch_image(preview_image_url)
    try:
        img = Image.open(io.BytesIO(data))
        if img.format and img.format.upper() != "PNG":
            out = io.BytesIO()
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            img.save(out, format="PNG")
            data = out.getvalue()
    except Exception as e:
        logger.warning(f"Could not convert image to PNG, returning raw: {e}")
    filename = "preview.png"
    return data, filename


def export_as_pdf(preview_urls: List[str], titles: Optional[List[str]] = None) -> bytes:
    """
    Fetch multiple preview images and combine into a single PDF.
    Uses img2pdf for lossless image embedding.
    """
    if not preview_urls:
        raise ValueError("At least one preview URL is required")
    if not HAS_IMG2PDF:
        raise RuntimeError("img2pdf not installed. Run: pip install img2pdf")

    images_data: List[bytes] = []
    for url in preview_urls:
        data = _fetch_image(url)
        # img2pdf expects JPEG or PNG
        try:
            img = Image.open(io.BytesIO(data))
            if img.format and img.format.upper() not in ("JPEG", "JPG", "PNG"):
                out = io.BytesIO()
                img.convert("RGB").save(out, format="PNG")
                data = out.getvalue()
        except Exception:
            pass
        images_data.append(data)

    pdf_bytes = img2pdf.convert(images_data)
    return pdf_bytes


def export_as_zip(
    preview_urls: List[str],
    titles: Optional[List[str]] = None,
    filename_prefix: str = "preview",
) -> bytes:
    """Fetch multiple preview images and return as ZIP archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, url in enumerate(preview_urls):
            try:
                data = _fetch_image(url)
                ext = "png"
                try:
                    img = Image.open(io.BytesIO(data))
                    if img.format:
                        ext = "jpg" if img.format.upper() in ("JPEG", "JPG") else "png"
                except Exception:
                    pass
                name = titles[i] if titles and i < len(titles) and titles[i] else f"page_{i+1}"
                safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name)[:50]
                zf.writestr(f"{filename_prefix}_{i+1}_{safe_name}.{ext}", data)
            except Exception as e:
                logger.warning(f"Skipping URL {url[:50]}...: {e}")
    return buf.getvalue()


def generate_embed_code(
    page_url: str,
    preview_image_url: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    width: str = "1200",
    height: str = "630",
) -> str:
    """
    Generate HTML embed code for CMS/blog integration.
    Returns a copy-paste ready snippet.
    """
    title = title or "Preview"
    desc = description or ""
    snippet = f'''<!-- MyMetaView Preview Embed -->
<a href="{page_url}" target="_blank" rel="noopener">
  <img src="{preview_image_url}" alt="{title}" width="{width}" height="{height}" loading="lazy" />
</a>
<!-- Optional: Open Graph meta tags for social sharing -->
<meta property="og:image" content="{preview_image_url}" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{desc}" />
<meta property="og:url" content="{page_url}" />'''
    return snippet
