from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, institutions, banks,
    fdrs, documents, workflows, notifications,
    dashboards, audit_logs, datasets, health
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & MFA"])
api_router.include_router(users.router, prefix="/users", tags=["User Administration"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["Institutions"])
api_router.include_router(banks.router, prefix="/banks", tags=["Banks"])
api_router.include_router(fdrs.router, prefix="/fdrs", tags=["FDR Records"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents & OCR"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows & Reviews"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards & Analytics"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Trails"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Synthetic Data"])
