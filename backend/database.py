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
    if not articles:
        return 0

    # Deduplicate by ID before sending to Supabase
    seen = {}
    for article in articles:
        seen[article["id"]] = article
    unique_articles = list(seen.values())

    removed = len(articles) - len(unique_articles)
    if removed > 0:
        logger.info(f"Removed {removed} duplicate articles before upsert")

    # Send in small batches of 50 to avoid payload limits
    batch_size = 50
    total_saved = 0

    for i in range(0, len(unique_articles), batch_size):
        batch = unique_articles[i:i + batch_size]
        try:
            response = (
                supabase.table("articles")
                .upsert(batch, on_conflict="id", ignore_duplicates=True)
                .execute()
            )
            count = len(response.data) if response.data else 0
            total_saved += count
            logger.info(f"Batch {i // batch_size + 1}: saved {count} articles")
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            continue

    logger.info(f"Total upserted: {total_saved} articles")
    return total_saved


def get_articles(category: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
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
