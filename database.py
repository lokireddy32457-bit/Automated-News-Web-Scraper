import os
import sqlite3
import hashlib
from datetime import datetime
import re

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "scraper.db")

# Stopwords for analytics keyword parsing
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'arent',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
    'can', 'cant', 'cannot', 'could', 'couldnt', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont',
    'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadnt', 'has', 'hasnt', 'have',
    'havent', 'having', 'he', 'hed', 'hell', 'hes', 'her', 'here', 'heres', 'hers', 'herself', 'him',
    'himself', 'his', 'how', 'hows', 'i', 'id', 'ill', 'im', 'ive', 'if', 'in', 'into', 'is', 'isnt',
    'it', 'its', 'itself', 'lets', 'me', 'more', 'most', 'mustnt', 'my', 'myself', 'no', 'nor', 'not',
    'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over',
    'own', 'same', 'shant', 'she', 'shed', 'shell', 'shes', 'should', 'shouldnt', 'so', 'some', 'such',
    'than', 'that', 'thats', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'theres',
    'these', 'they', 'theyd', 'theyll', 'theyre', 'theyve', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'wasnt', 'we', 'wed', 'well', 'were', 'weve', 'werent',
    'what', 'whats', 'when', 'whens', 'where', 'wheres', 'which', 'while', 'who', 'whos', 'whom', 'why',
    'whys', 'with', 'wont', 'would', 'wouldnt', 'you', 'youd', 'youll', 'youre', 'youve', 'your', 'yours',
    'yourself', 'yourselves', 'us', 'new', 'show', 'ask', 'tech', 'how', 'why', 'what'
}

def get_db_connection():
    """Establishes a thread-safe connection to the SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema and indices if they do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                category TEXT,
                scraped_at TEXT NOT NULL,
                published_at TEXT
            )
        """)
        
        # Create scrape logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                articles_scraped INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                error_message TEXT
            )
        """)
        
        # Create indices for search optimization
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON articles(scraped_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_hash_id ON articles(hash_id)")
        
        conn.commit()

def save_article(title, url, source, category=None, published_at=None):
    """
    Saves an article to the database. Generates a unique hash_id based on the URL
    to prevent duplicate article records.
    
    Returns True if a new article was inserted, False if it was a duplicate.
    """
    if not title or not url:
        return False
        
    # Generate cryptographic hash based on normalized URL to avoid duplicates
    normalized_url = url.strip().lower()
    hash_id = hashlib.md5(normalized_url.encode('utf-8')).hexdigest()
    
    scraped_at = datetime.now().isoformat()
    
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO articles (hash_id, title, url, source, category, scraped_at, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (hash_id, title.strip(), url.strip(), source.strip(), category, scraped_at, published_at)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        # Expected duplicate record based on hash_id unique constraint
        return False
    except Exception as e:
        print(f"Error saving article: {e}")
        return False

def get_articles(keyword=None, source=None, limit=100, offset=0):
    """
    Fetches articles from the database based on optional filters.
    Returns list of dicts.
    """
    query = "SELECT * FROM articles WHERE 1=1"
    params = []
    
    if keyword:
        query += " AND (title LIKE ? OR category LIKE ?)"
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
        
    if source:
        query += " AND source = ?"
        params.append(source)
        
    query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error querying articles: {e}")
        return []

def get_article_count(keyword=None, source=None):
    """Returns the total number of articles matching filters."""
    query = "SELECT COUNT(*) FROM articles WHERE 1=1"
    params = []
    
    if keyword:
        query += " AND (title LIKE ? OR category LIKE ?)"
        params.append(f"%{keyword}%")
        params.append(f"%{keyword}%")
        
    if source:
        query += " AND source = ?"
        params.append(source)
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()[0]
    except Exception as e:
        print(f"Error getting article count: {e}")
        return 0

def log_scrape_run(source, articles_scraped, status, error_message=None):
    """Inserts a run diagnostic log record into the scrape_logs table."""
    timestamp = datetime.now().isoformat()
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO scrape_logs (source, articles_scraped, status, timestamp, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source, articles_scraped, status, timestamp, error_message)
            )
            conn.commit()
    except Exception as e:
        print(f"Error logging scrape run: {e}")

def get_scrape_logs(limit=10):
    """Retrieves recent scrape operation logs."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scrape_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error querying logs: {e}")
        return []

def get_analytics_summary():
    """
    Performs analytical computations for visual reports.
    Returns aggregates of sources and top article title keywords.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Total articles by source
            cursor.execute("SELECT source, COUNT(*) as count FROM articles GROUP BY source")
            sources = [dict(row) for row in cursor.fetchall()]
            
            # 2. Daily scraping volume over the last 14 days
            cursor.execute("""
                SELECT strftime('%Y-%m-%d', scraped_at) as date, COUNT(*) as count 
                FROM articles 
                GROUP BY date 
                ORDER BY date DESC 
                LIMIT 14
            """)
            daily_volumes = [dict(row) for row in cursor.fetchall()]
            daily_volumes.reverse() # Chronological order
            
            # 3. Top keywords parsed from headlines
            cursor.execute("SELECT title FROM articles")
            titles = [row['title'] for row in cursor.fetchall()]
            
            word_counts = {}
            for title in titles:
                # Basic tokenization
                words = re.findall(r'[a-zA-Z]{3,}', title.lower())
                for word in words:
                    if word not in STOPWORDS:
                        word_counts[word] = word_counts.get(word, 0) + 1
            
            # Get top 15 keywords
            sorted_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:15]
            keywords = [{"word": k, "count": v} for k, v in sorted_keywords]
            
            return {
                "sources": sources,
                "daily_volumes": daily_volumes,
                "keywords": keywords,
                "total_count": sum(s['count'] for s in sources)
            }
    except Exception as e:
        print(f"Error computing analytics: {e}")
        return {"sources": [], "daily_volumes": [], "keywords": [], "total_count": 0}

if __name__ == "__main__":
    # Test DB initialization
    init_db()
    print("Database successfully initialized at:", DB_PATH)
