from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import check_db_connection
from app.auth.router import router as auth_router
from app.routes.coding import router as coding_router
from app.routes.interview import router as interview_router
from app.routes.ats import router as ats_router
from app.routes.jobs import router as jobs_router
from app.routes.scraped_content import router as scraped_content_router

# Import scrapers to run on startup/intervals
from app.scrapers.coding_scraper import scrape_coding_problems
from app.scrapers.roadmap_scraper import scrape_roadmaps
from app.scrapers.aptitude_scraper import scrape_aptitude_questions
from app.scrapers.interview_scraper import scrape_interview_questions
from app.scrapers.opportunities_scraper import scrape_opportunities

logger = logging.getLogger("app.main")

async def run_all_scrapers_pipeline():
    """Background task executing the complete live/static aggregation pipeline."""
    logger.info("Initializing auto-refresh web scraper pipeline...")
    try:
        await scrape_coding_problems()
        await scrape_roadmaps()
        await scrape_aptitude_questions()
        await scrape_interview_questions()
        await scrape_opportunities()
        logger.info("Auto-refresh web scraper pipeline executed successfully.")
    except Exception as e:
        logger.error(f"Error during scheduled auto-refresh run: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Check database connection
    await check_db_connection()
    
    # Launch scraper pipeline immediately in background to prevent FastAPI startup delay
    asyncio.create_task(run_all_scrapers_pipeline())
    
    # Configure 12-hour background scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_all_scrapers_pipeline, 'interval', hours=12)
    scheduler.start()
    
    yield
    # Shutdown: Stop scheduled jobs cleanly
    scheduler.shutdown()

app = FastAPI(
    title="PlacementCrack Backend",
    description="Industry-grade Placement Preparation platform API endpoints.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware for Frontend Integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend URLs (like Vercel domain)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under the /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(coding_router, prefix="/api")
app.include_router(interview_router, prefix="/api")
app.include_router(ats_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(scraped_content_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "status": "Online",
        "message": "Welcome to the PlacementCrack API. Navigate to /docs for API documentation.",
        "version": "1.0.0"
    }
