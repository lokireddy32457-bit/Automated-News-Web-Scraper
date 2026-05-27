import sys
import os
import argparse
import csv
from datetime import datetime
import database
import scraper

# ANSI Color constants for terminal formatting
COLOR_HEADER = "\033[95m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_WARNING = "\033[93m"
COLOR_FAIL = "\033[91m"
COLOR_END = "\033[0m"
COLOR_BOLD = "\033[1m"

def print_banner():
    banner = f"""
{COLOR_CYAN}{COLOR_BOLD}=======================================================
    AUTOMATED NEWS WEB SCRAPER CONTROLLER
======================================================={COLOR_END}
    """
    print(banner)

def handle_scrape(args):
    """Triggers a real-time scrape across all active scraper engines."""
    print(f"{COLOR_BLUE}[+] Initializing active scraping engines...{COLOR_END}\n")
    results = scraper.run_all_scrapers()
    print(f"\n{COLOR_GREEN}[SUCCESS] Crawl sequence finished! Extracted and stored {len(results)} records.{COLOR_END}")

def handle_list(args):
    """Retrieves and prints stored headlines in a neat terminal layout."""
    articles = database.get_articles(keyword=args.keyword, source=args.source, limit=args.limit)
    if not articles:
        print(f"{COLOR_WARNING}[!] No records found matching current query parameters.{COLOR_END}")
        return
        
    print(f"\n{COLOR_BOLD}{'ID':<4} | {'SOURCE':<12} | {'CATEGORY':<14} | {'TITLE':<60}{COLOR_END}")
    print("-" * 100)
    for art in articles:
        title = art['title']
        if len(title) > 57:
            title = title[:57] + "..."
        print(f"{art['id']:<4} | {art['source']:<12} | {art['category']:<14} | {title:<60}")
    print(f"\n{COLOR_GREEN}[INFO] Displaying {len(articles)} recent records.{COLOR_END}")

def handle_stats(args):
    """Computes and illustrates quick database analytics in the console."""
    summary = database.get_analytics_summary()
    logs = database.get_scrape_logs(limit=5)
    
    print(f"\n{COLOR_HEADER}=== DATABASE METRICS ==={COLOR_END}")
    print(f"Total articles harvested: {COLOR_BOLD}{summary['total_count']}{COLOR_END}")
    
    print(f"\n{COLOR_BLUE}--- Feed breakdown ---{COLOR_END}")
    for src in summary['sources']:
        print(f" * {src['source']:<15} : {src['count']} headlines")
        
    print(f"\n{COLOR_BLUE}--- Top 10 Keywords ---{COLOR_END}")
    for idx, kw in enumerate(summary['keywords'][:10], 1):
        print(f" {idx:<2}. {kw['word']:<15} ({kw['count']} occurrences)")
        
    print(f"\n{COLOR_BLUE}--- Last 5 Runs ---{COLOR_END}")
    print(f"{'TIMESTAMP':<25} | {'SOURCE':<12} | {'SAVED':<6} | {'STATUS':<8}")
    print("-" * 60)
    for log in logs:
        # Format ISO timestamp for display
        dt = log['timestamp'][:19].replace('T', ' ')
        status_color = COLOR_GREEN if log['status'] == "SUCCESS" else COLOR_FAIL
        print(f"{dt:<25} | {log['source']:<12} | {log['articles_scraped']:<6} | {status_color}{log['status']:<8}{COLOR_END}")

def handle_export(args):
    """Exports structured database files directly to CSV on local filesystem."""
    filepath = args.output
    if not filepath.endswith('.csv'):
        filepath += ".csv"
        
    articles = database.get_articles(limit=10000)
    if not articles:
        print(f"{COLOR_WARNING}[!] Database is empty. Scrape data before exporting.{COLOR_END}")
        return
        
    print(f"{COLOR_BLUE}[+] Extracting articles to structured CSV: {filepath}...{COLOR_END}")
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Title", "URL", "Source", "Category", "Scraped At", "Published At"])
            for idx, art in enumerate(articles, start=1):
                writer.writerow([
                    idx,
                    art['title'],
                    art['url'],
                    art['source'],
                    art['category'],
                    art['scraped_at'],
                    art['published_at']
                ])
        print(f"{COLOR_GREEN}[SUCCESS] Data successfully written to {os.path.abspath(filepath)}! Ready for downstream analytics.{COLOR_END}")
    except Exception as e:
        print(f"{COLOR_FAIL}[ERROR] File export failed: {e}{COLOR_END}")

def main():
    database.init_db()
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="Automated Web Scraper - Enterprise command line controller.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)
    
    # Scrape Command
    subparsers.add_parser('scrape', help='Triggers immediate scraper execution across all feeds.')
    
    # List Command
    list_parser = subparsers.add_parser('list', help='Prints stored article records in high fidelity tabular layout.')
    list_parser.add_argument('--limit', type=int, default=20, help='Maximum rows to print (default: 20)')
    list_parser.add_argument('--source', type=str, choices=['Hacker News', 'BBC Tech'], help='Filter headlines by source.')
    list_parser.add_argument('--keyword', type=str, help='Filter headlines by a keyword matching title.')
    
    # Stats Command
    subparsers.add_parser('stats', help='Displays database summary metrics and run history logs.')
    
    # Export Command
    export_parser = subparsers.add_parser('export', help='Exports full database contents to a structured CSV file.')
    export_parser.add_argument('output', type=str, help='Output path for the generated CSV file (e.g. data_headlines.csv).')
    
    args = parser.parse_args()
    
    if args.command == 'scrape':
        handle_scrape(args)
    elif args.command == 'list':
        handle_list(args)
    elif args.command == 'stats':
        handle_stats(args)
    elif args.command == 'export':
        handle_export(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{COLOR_WARNING}[!] Process interrupted by user.{COLOR_END}")
        sys.exit(0)
