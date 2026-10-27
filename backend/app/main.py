import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.v1.api import api_router
from app.services.notification_service import check_fdr_maturity_alerts
from app.services.anomaly_detector import AnomalyDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scheduler for scheduled maturity checks
scheduler = BackgroundScheduler()

def scheduled_maturity_job():
    """Periodic job to calculate approaching maturity dates and send in-app alerts."""
    db = SessionLocal()
    try:
        count = check_fdr_maturity_alerts(db)
        if count > 0:
            logger.info(f"[SCHEDULER] Generated {count} new maturity notifications.")
    except Exception as e:
        logger.error(f"[SCHEDULER ERROR] Failed checking maturity alerts: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables are created
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    
    # Initialize ML anomaly model baseline
    try:
        AnomalyDetector.load_or_train_baseline()
        logger.info("Anomaly detection engine initialized.")
    except Exception as e:
        logger.warning(f"Anomaly detector initialization notice: {e}")

    # Start Background Scheduler
    if settings.ENABLE_BACKGROUND_SCHEDULER:
        scheduler.add_job(scheduled_maturity_job, "interval", hours=12, id="maturity_alerts", replace_existing=True)
        scheduler.start()
        logger.info("Background maturity alert scheduler started.")

    yield

    # Shutdown
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped.")

app = FastAPI(
    title="FDR SmartTrack API",
    description="SIH26265 Smart Security Deposit / Fixed Deposit Receipt Management Portal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploaded documents
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "project": "FDR SmartTrack",
        "description": "Security Deposit / FDR Management Portal (SIH26265)",
        "api_docs": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the system administrator."}
    )
