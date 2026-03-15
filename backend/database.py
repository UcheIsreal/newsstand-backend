import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)


def upsert_articles(articles: list[dict]) -> int:
    """
    Insert new articles into Supabase.
    Uses 'id' (MD5 of URL) as the unique key — skips duplicates automatically.
    Returns the count of successfully upserted articles.
    """
    if not articles:
        return 0

    try:
        response = (
            supabase.table("articles")
            .upsert(articles, on_conflict="id")
            .execute()
        )
        count = len(response.data) if response.data else 0
        logger.info(f"Upserted {count} articles to Supabase")
        return count
    except Exception as e:
        logger.error(f"Supabase upsert failed: {e}")
        raise


def get_articles(category: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """Fetch articles from Supabase, optionally filtered by category."""
    try:
        query = (
            supabase.table("articles")
            .select("*")
            .order("published_at", desc=True)
            .limit(limit)
            .offset(offset)
        )
        if category:
            query = query.eq("category", category)

        response = query.execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Supabase fetch failed: {e}")
        raise
