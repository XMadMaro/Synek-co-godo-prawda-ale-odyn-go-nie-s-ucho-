"""Audit API routes."""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, HttpUrl

router = APIRouter()


class AuditRequestBody(BaseModel):
    """Request body for starting an audit."""
    target_url: HttpUrl
    scrape_depth: int = 2
    questions_count: int = 20


class AuditResponse(BaseModel):
    """Response after starting an audit."""
    audit_id: str
    status: str
    message: str


@router.post("/audit", response_model=AuditResponse)
async def start_audit(
    request: AuditRequestBody,
    background_tasks: BackgroundTasks,
):
    """
    Start a new chatbot audit.

    This endpoint initiates the full audit pipeline:
    1. Scraping the target website
    2. Indexing content into RAG
    3. Generating test questions
    4. Interrogating the chatbot
    5. Judging responses
    6. Generating report
    """
    # TODO: Implement actual audit logic
    # background_tasks.add_task(run_audit, request)

    return AuditResponse(
        audit_id="audit_placeholder",
        status="queued",
        message=f"Audit for {request.target_url} has been queued",
    )


@router.get("/audit/{audit_id}")
async def get_audit_status(audit_id: str):
    """Get the status of an audit."""
    # TODO: Implement status retrieval from database

    return {
        "audit_id": audit_id,
        "status": "unknown",
        "progress": 0,
        "message": "Not implemented yet",
    }


@router.get("/audit/{audit_id}/report")
async def get_audit_report(audit_id: str):
    """Get the full audit report."""
    # TODO: Implement report retrieval

    raise HTTPException(
        status_code=404,
        detail=f"Report for audit {audit_id} not found",
    )
