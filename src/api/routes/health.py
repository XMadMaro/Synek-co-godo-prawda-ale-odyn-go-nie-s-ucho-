"""Health check routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "truthseeker",
        "version": "0.1.0",
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    TODO: Check database, Qdrant, Redis connections.
    """
    checks = {
        "postgres": "unknown",
        "qdrant": "unknown",
        "redis": "unknown",
    }

    # TODO: Implement actual checks
    all_ready = True  # Placeholder

    return {
        "ready": all_ready,
        "checks": checks,
    }
