import requests
from bs4 import BeautifulSoup
from src.config import settings
import logging

logger = logging.getLogger(__name__)

def scrape_url(url: str) -> str:
    """
    Scrapes a webpage and extracts clean text, ignoring scripts and styles.
    Includes advanced headers to bypass basic anti-bot protections.
    """
    logger.info(f"Scraping URL: {url}")
    
    # A robust set of headers making us look like a standard desktop browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }
    
    try:
        # Added a longer timeout as some sites delay responses to suspected bots
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script_or_style in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script_or_style.extract()
            
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return clean_text[:settings.MAX_SCRAPE_CHARS]
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error scraping {url}: {e}")
        return ""
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return ""