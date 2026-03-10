"""
Export & embed routes for MyMetaView 4.0 P7.
PNG, PDF, embed code, ZIP download flows.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, HttpUrl

from backend.services.export_service import (
    export_as_png,
    export_as_pdf,
    export_as_zip,
    generate_embed_code,
)
from backend.jobs.demo_batch_job import get_batch_data

router = APIRouter(prefix="/demo-v2", tags=["demo", "export"])


class ExportPdfRequest(BaseModel):
    """Request body for PDF export."""
    preview_urls: List[str]
    titles: Optional[List[str]] = None


class ExportZipRequest(BaseModel):
    """Request body for ZIP export."""
    preview_urls: List[str]
    titles: Optional[List[str]] = None
    filename_prefix: str = "preview"


class EmbedCodeRequest(BaseModel):
    """Request for embed code generation."""
    page_url: str
    preview_image_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    width: str = "1200"
    height: str = "630"


@router.get("/export/png")
def download_png(
    preview_url: str = Query(..., description="URL of the preview image to download"),
):
    """
    Download a single preview image as PNG.
    Use the composited_preview_image_url or preview_image_url from job/batch results.
    """
    try:
        data, filename = export_as_png(preview_url)
        return Response(
            content=data,
            media_type="image/png",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch or convert image: {str(e)}",
        )


@router.post("/export/pdf")
def download_pdf(request: ExportPdfRequest):
    """
    Export multiple preview images as a single PDF.
    Max 50 URLs per request.
    """
    if len(request.preview_urls) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 previews per PDF.",
        )
    try:
        pdf_bytes = export_as_pdf(request.preview_urls, request.titles)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="previews.pdf"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate PDF: {str(e)}",
        )


@router.post("/export/zip")
def download_zip(request: ExportZipRequest):
    """
    Export multiple preview images as a ZIP archive.
    Max 50 URLs per request.
    """
    if len(request.preview_urls) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 previews per ZIP.",
        )
    try:
        zip_bytes = export_as_zip(
            request.preview_urls,
            request.titles,
            request.filename_prefix,
        )
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="previews.zip"'},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate ZIP: {str(e)}",
        )


@router.get("/export/zip/batch/{batch_id}")
def download_zip_from_batch(batch_id: str):
    """
    Export all completed previews from a batch job as ZIP.
    Returns 202 if batch is still running.
    """
    data = get_batch_data(batch_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found.",
        )
    if data["status"] not in ("completed", "failed"):
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Batch still running. Poll /demo-v2/batch/{batch_id}/results first.",
        )
    urls = []
    titles = []
    for r in data["results"]:
        url = r.get("preview_image_url") or r.get("screenshot_url")
        if url and not r.get("error"):
            urls.append(url)
            titles.append(r.get("title"))
    if not urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed previews to export.",
        )
    try:
        zip_bytes = export_as_zip(urls, titles, f"batch_{batch_id[:8]}")
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="previews.zip"'},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate ZIP: {str(e)}",
        )


@router.post("/embed-code", response_model=dict)
def get_embed_code(request: EmbedCodeRequest):
    """
    Generate copy-paste embed code for CMS/blog integration.
    Returns HTML snippet with img tag and optional Open Graph meta tags.
    """
    snippet = generate_embed_code(
        request.page_url,
        request.preview_image_url,
        request.title,
        request.description,
        request.width,
        request.height,
    )
    return {
        "embed_code": snippet,
        "page_url": request.page_url,
        "preview_image_url": request.preview_image_url,
    }
