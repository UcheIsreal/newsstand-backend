import feedparser
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from sources import SOURCES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_date(entry) -> str:
    """Parse published date from feed entry."""
    for attr in ["published_parsed", "updated_parsed"]:
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def get_excerpt(entry) -> str:
    """Extract the best available excerpt from a feed entry."""
    # Try summary first, then content, then description
    if hasattr(entry, "summary") and entry.summary:
        text = entry.summary
    elif hasattr(entry, "content") and entry.content:
        text = entry.content[0].get("value", "")
    elif hasattr(entry, "description") and entry.description:
        text = entry.description
    else:
        return ""

    # Strip basic HTML tags
    import re
    text = re.sub(r"<[^>]+>", "", text).strip()

    # Truncate to ~300 chars at a word boundary
    if len(text) > 300:
        text = text[:300].rsplit(" ", 1)[0] + "..."

    return text


def get_image(entry) -> Optional[str]:
    """Try to extract a thumbnail/image URL from the feed entry."""
    # media:thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    # media:content
    if hasattr(entry, "media_content") and entry.media_content:
        for mc in entry.media_content:
            if mc.get("medium") == "image" or mc.get("url", "").endswith((".jpg", ".png", ".webp")):
                return mc.get("url")
    # enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if "image" in enc.get("type", ""):
                return enc.get("url")
    return None


def make_id(url: str) -> str:
    """Generate a stable unique ID from the article URL."""
    return hashlib.md5(url.encode()).hexdigest()


def fetch_category(category: str) -> list[dict]:
    """Fetch and parse all RSS feeds for a given category."""
    articles = []
    sources = SOURCES.get(category, [])

    for source in sources:
        try:
            logger.info(f"Fetching: {source['name']}")
            feed = feedparser.parse(source["url"])

            if feed.bozo and not feed.entries:
                logger.warning(f"  Feed error for {source['name']}: {feed.bozo_exception}")
                continue

            for entry in feed.entries[:10]:  # Max 10 articles per source
                url = entry.get("link", "")
                if not url:
                    continue

                article = {
                    "id": make_id(url),
                    "title": entry.get("title", "").strip(),
                    "excerpt": get_excerpt(entry),
                    "url": url,
                    "source_name": source["name"],
                    "source_logo": source["logo"],
                    "category": category,
                    "image_url": get_image(entry),
                    "published_at": parse_date(entry),
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "tags": [t.get("term", "") for t in entry.get("tags", []) if t.get("term")][:5],
                }
                articles.append(article)

        except Exception as e:
            logger.error(f"  Failed to fetch {source['name']}: {e}")
            continue

    logger.info(f"  [{category}] Fetched {len(articles)} articles")
    return articles


def fetch_all() -> list[dict]:
    """Fetch all categories and return combined article list."""
    all_articles = []
    for category in SOURCES:
        all_articles.extend(fetch_category(category))
    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles
