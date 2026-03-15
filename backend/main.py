from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from feed_fetcher import fetch_all
from database import upsert_articles, get_articles
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_fetch_job():
    """Scheduled job: fetch all feeds and save to Supabase."""
    logger.info("Running scheduled feed fetch...")
    articles = fetch_all()
    upsert_articles(articles)
    logger.info("Feed fetch complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run once on startup
    await run_fetch_job()

    # Schedule every 30 minutes
    scheduler.add_job(run_fetch_job, "interval", minutes=30)
    scheduler.start()
    logger.info("Scheduler started — fetching feeds every 30 minutes.")

    yield

    scheduler.shutdown()


app = FastAPI(title="Newsstand API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock this down to your Vercel domain in production
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "Newsstand API is running"}


@app.get("/articles")
def list_articles(
    category: str = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Returns paginated articles, optionally filtered by category.
    Example: GET /articles?category=sports&limit=20&offset=0
    """
    try:
        articles = get_articles(category=category, limit=limit, offset=offset)
        return {"articles": articles, "count": len(articles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch")
async def trigger_fetch():
    """Manually trigger a feed fetch (useful for testing)."""
    await run_fetch_job()
    return {"status": "ok", "message": "Feed fetch triggered"}


@app.get("/categories")
def list_categories():
    from sources import SOURCES
    return {"categories": list(SOURCES.keys())}
