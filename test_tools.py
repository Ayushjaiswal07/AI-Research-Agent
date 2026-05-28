from src.tools.web_search import search_web
from src.tools.scraper import scrape_url

def main():
    print("--- Testing Web Search ---")
    query = "Latest capabilities of Gemini 1.5 Pro AI"
    results = search_web(query, max_results=3)
    
    if not results:
        print("Search failed or returned no results.")
        return

    for i, res in enumerate(results):
        print(f"\nResult {i+1}: {res['title']}")
        print(f"URL: {res['link']}")
        print(f"Snippet: {res['snippet']}")
    
    print("\n--- Testing Web Scraper (with Fallback) ---")
    
    # Agentic behavior: Try links until one works
    for res in results:
        url = res['link']
        print(f"\nAttempting to scrape: {url}...")
        scraped_text = scrape_url(url)
        
        if scraped_text:
            print("\n✅ Scraping Successful! Here are the first 500 characters:")
            print("-" * 50)
            print(scraped_text[:500] + "...\n[TRUNCATED]")
            print("-" * 50)
            print(f"Total characters scraped: {len(scraped_text)}")
            break # Exit loop once we successfully get data
        else:
            print(f"❌ Failed to scrape {url}. Moving to next result...")

if __name__ == "__main__":
    main()