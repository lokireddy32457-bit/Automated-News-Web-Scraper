import re
import random
import time
import warnings
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from datetime import datetime
import database

# Suppress BS4 XML-parsed-as-HTML warning for RSS feeds
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# List of rotating modern User-Agents for stealth and compliance
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0"
]

class BaseScraper:
    """Abstract base scraper to define structured lifecycle methods."""
    def __init__(self, source_name):
        self.source_name = source_name
        self.session = requests.Session()
        
    def get_headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive"
        }

    def fetch_url(self, url, retries=3, backoff=2):
        """Fetches URL contents using automatic retries and exponential backoff."""
        for attempt in range(1, retries + 1):
            try:
                # Politeness rate-limit delay
                time.sleep(random.uniform(0.5, 1.5))
                
                response = self.session.get(url, headers=self.get_headers(), timeout=10)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"[{self.source_name}] Attempt {attempt} returned status code: {response.status_code}")
            except requests.RequestException as e:
                print(f"[{self.source_name}] Attempt {attempt} failed: {e}")
            
            if attempt < retries:
                sleep_time = backoff ** attempt
                print(f"[{self.source_name}] Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
                
        return None

    def scrape(self):
        """Executes scraping, returns parsed articles list, and logs status to DB."""
        print(f"[{self.source_name}] Initiating real-time scrape extraction...")
        try:
            articles = self.extract_articles()
            if articles is None:
                database.log_scrape_run(self.source_name, 0, "FAILED", "Extraction returned None")
                return []
                
            inserted_count = 0
            for art in articles:
                # Save to database and track new inserts vs duplicates
                success = database.save_article(
                    title=art.get('title'),
                    url=art.get('url'),
                    source=self.source_name,
                    category=art.get('category'),
                    published_at=art.get('published_at')
                )
                if success:
                    inserted_count += 1
            
            database.log_scrape_run(self.source_name, inserted_count, "SUCCESS")
            print(f"[{self.source_name}] Scrape completed. Extracted {len(articles)} articles, Saved {inserted_count} new entries.")
            return articles
        except Exception as e:
            err_msg = str(e)
            database.log_scrape_run(self.source_name, 0, "FAILED", err_msg)
            print(f"[{self.source_name}] Scrape failure: {err_msg}")
            return []

    def extract_articles(self):
        raise NotImplementedError("Subclasses must implement extract_articles()")


class HackerNewsScraper(BaseScraper):
    """Scrapes trending tech stories from Hacker News home page."""
    def __init__(self):
        super().__init__("Hacker News")
        self.url = "https://news.ycombinator.com/"

    def extract_articles(self):
        html_content = self.fetch_url(self.url)
        if not html_content:
            return None
            
        soup = BeautifulSoup(html_content, "html.parser")
        articles = []
        
        # Hacker news lists articles inside rows of class 'athing'
        rows = soup.select("tr.athing")
        for row in rows:
            try:
                title_td = row.select_one("td.title span.titleline > a")
                if not title_td:
                    # Could be custom title structure or ads
                    continue
                    
                title = title_td.text.strip()
                url = title_td.get("href", "")
                
                # Check for relative link on HN and resolve it
                if url.startswith("item?id="):
                    url = f"https://news.ycombinator.com/{url}"
                
                # Try to extract category (e.g. Show HN, Ask HN, Launch HN, or default Tech)
                category = "General"
                if title.lower().startswith("show hn:"):
                    category = "Show HN"
                elif title.lower().startswith("ask hn:"):
                    category = "Ask HN"
                elif title.lower().startswith("launch hn:"):
                    category = "Launch HN"
                else:
                    category = "Tech News"
                
                articles.append({
                    "title": title,
                    "url": url,
                    "category": category,
                    "published_at": datetime.now().isoformat()
                })
            except Exception as e:
                print(f"[Hacker News] Error parsing article row: {e}")
                
        return articles


class BBCTechScraper(BaseScraper):
    """Scrapes latest headlines from BBC News Technology syndication feed."""
    def __init__(self):
        super().__init__("BBC Tech")
        # BBC Technology RSS feed is highly reliable and clean for structured parsing
        self.url = "https://feeds.bbci.co.uk/news/technology/rss.xml"

    def extract_articles(self):
        xml_content = self.fetch_url(self.url)
        if not xml_content:
            return None
            
        soup = BeautifulSoup(xml_content, "html.parser") # standard html parser can parse clean RSS structures well
        articles = []
        
        items = soup.find_all("item")
        for item in items:
            try:
                title_node = item.find("title")
                link_node = item.find("link")
                pub_date_node = item.find("pubdate")
                desc_node = item.find("description")
                
                if not title_node or not link_node:
                    continue
                
                # Clean up html tags or CDATA from RSS nodes
                title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title_node.text).strip()
                # Clean up title if BeautifulSoup parsed RSS tags
                title = title.replace("<![CDATA[", "").replace("]]>", "")
                
                url = link_node.text.strip().replace("<![CDATA[", "").replace("]]>", "")
                
                pub_date = pub_date_node.text.strip() if pub_date_node else ""
                
                category = "Tech Headline"
                # Infer subcategory from description
                desc_text = desc_node.text.lower() if desc_node else ""
                if "ai" in desc_text or "artificial intelligence" in desc_text or "chatgpt" in desc_text:
                    category = "AI / ML"
                elif "cyber" in desc_text or "hack" in desc_text or "security" in desc_text:
                    category = "Cybersecurity"
                elif "phone" in desc_text or "apple" in desc_text or "samsung" in desc_text or "device" in desc_text:
                    category = "Gadgets"
                elif "game" in desc_text or "console" in desc_text or "playstation" in desc_text:
                    category = "Gaming"
                
                articles.append({
                    "title": title,
                    "url": url,
                    "category": category,
                    "published_at": pub_date
                })
            except Exception as e:
                print(f"[BBC Tech] Error parsing RSS item: {e}")
                
        return articles


def run_all_scrapers():
    """Runs all registered scrapers and aggregates results."""
    scrapers = [HackerNewsScraper(), BBCTechScraper()]
    aggregated_results = []
    
    for scraper in scrapers:
        results = scraper.scrape()
        aggregated_results.extend(results)
        # Polite spacing between targets
        time.sleep(1)
        
    return aggregated_results

if __name__ == "__main__":
    # Test Scraper local run
    database.init_db()
    results = run_all_scrapers()
    print(f"\nTest Run complete. Extracted total {len(results)} headlines.")
