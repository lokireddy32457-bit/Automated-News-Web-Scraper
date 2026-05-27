import os
import csv
import io
from flask import Flask, jsonify, request, render_template, Response
import database
import scraper
from scheduler import scheduler_instance

app = Flask(__name__)

# Ensure Database is initialized on startup
database.init_db()

# Auto-start scheduler with a default 15 minute interval (900 seconds)
scheduler_instance.start(interval_seconds=900)

@app.route("/")
def index():
    """Renders the main glassmorphism analytics dashboard."""
    return render_template("index.html")

@app.route("/api/articles", methods=["GET"])
def get_articles_api():
    """API endpoint to query, search, and paginate scraped headlines."""
    keyword = request.args.get("q", "").strip()
    source = request.args.get("source", "").strip()
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    
    # Standardize empty values
    keyword_filter = keyword if keyword else None
    source_filter = source if source else None
    
    articles = database.get_articles(keyword=keyword_filter, source=source_filter, limit=limit, offset=offset)
    total_records = database.get_article_count(keyword=keyword_filter, source=source_filter)
    
    return jsonify({
        "success": True,
        "articles": articles,
        "total": total_records,
        "limit": limit,
        "offset": offset
    })

@app.route("/api/scrape", methods=["POST"])
def trigger_scrape_api():
    """Endpoint to trigger real-time scraper on demand."""
    try:
        results = scraper.run_all_scrapers()
        return jsonify({
            "success": True,
            "message": "Scrape completed successfully",
            "articles_scraped": len(results)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/analytics", methods=["GET"])
def get_analytics_api():
    """Downstream analytics endpoint serving metrics for Chart.js rendering."""
    summary = database.get_analytics_summary()
    logs = database.get_scrape_logs(limit=10)
    
    return jsonify({
        "success": True,
        "analytics": summary,
        "logs": logs
    })

@app.route("/api/scheduler", methods=["GET", "POST"])
def manage_scheduler_api():
    """Manages background scraper worker parameters."""
    if request.method == "POST":
        data = request.json or {}
        action = data.get("action", "")
        
        if action == "start":
            interval = int(data.get("interval", 900))
            scheduler_instance.start(interval_seconds=interval)
        elif action == "stop":
            scheduler_instance.stop()
        elif action == "set_interval":
            interval = int(data.get("interval", 900))
            scheduler_instance.set_interval(interval_seconds=interval)
            
    return jsonify({
        "success": True,
        "running": scheduler_instance.running,
        "interval": scheduler_instance.interval,
        "last_run_time": scheduler_instance.last_run_time
    })

@app.route("/api/export", methods=["GET"])
def export_csv_api():
    """
    Exports filtered headlines into highly-structured CSV format 
    on the fly for downstream business analytics.
    """
    keyword = request.args.get("q", "").strip()
    source = request.args.get("source", "").strip()
    
    keyword_filter = keyword if keyword else None
    source_filter = source if source else None
    
    # Retrieve all records matching selection filters
    articles = database.get_articles(keyword=keyword_filter, source=source_filter, limit=10000, offset=0)
    
    # Create in-memory string buffer for CSV generation
    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Write CSV Header
    writer.writerow(["ID", "Title", "URL", "Source", "Category", "Scraped At", "Published At"])
    
    # Write article rows
    for index, art in enumerate(articles, start=1):
        writer.writerow([
            index,
            art.get("title", ""),
            art.get("url", ""),
            art.get("source", ""),
            art.get("category", ""),
            art.get("scraped_at", ""),
            art.get("published_at", "")
        ])
        
    # Generate CSV response
    response_data = output.getvalue()
    output.close()
    
    filename = f"scraped_headlines_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        response_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache"
        }
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting flask server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
