from ddgs import DDGS
from typing import List, Dict
from src.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = settings.MAX_SEARCH_RESULTS) -> List[Dict[str, str]]:
    """
    Searches the web using DDGS and returns a list of results.
    """
    logger.info(f"Executing web search for: '{query}'")
    try:
        # The new ddgs package doesn't require a context manager
        results = DDGS().text(query, max_results=max_results)
            
        formatted_results = []
        for res in results:
            # Safely get keys, as the dictionary structure sometimes varies slightly
            formatted_results.append({
                "title": res.get("title", ""),
                "link": res.get("href", "") or res.get("link", ""),
                "snippet": res.get("body", "") or res.get("snippet", "")
            })
            
        return formatted_results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []