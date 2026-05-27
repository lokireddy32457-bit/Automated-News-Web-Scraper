# 🪐 AURA Scraper - Automated News Web Scraper & Analytics Dashboard

A professional, enterprise-grade automated web scraping engine and downstream data intelligence dashboard built with Python, BeautifulSoup4, SQLite, and Flask. It automates real-time information gathering from popular news platforms (Hacker News and BBC News Tech), parses unstructured HTML into indexed relational schemas, and renders a stunning glassmorphic dashboard with live data visualizations.

---

## ✨ Features

* **🔌 Core Scraper Engines**: Fully modular scrapers for ycombinator (Hacker News DOM parsing) and BBC Tech (RSS XML parsing).
* **🛡️ Stealth & Politeness Compliance**: Implements request spacing, rotating modern browser `User-Agents`, and automatic exponential retry backoffs.
* **📈 Downstream Analytics**: Aggregates statistical metrics and parses headline vocabulary to compute top keyword frequencies.
* **📊 Glassmorphic Web Dashboard**: Rich dark-mode interface utilizing glowing animated canvas gradients, interactive responsive grid cards, search filters, and Chart.js animations.
* **💾 Duplicate Prevention**: Encodes cryptographically secure URL MD5 hashes to prevent duplicate database pollution.
* **💻 CommandLine Interface (CLI)**: High-fidelity terminal controller for direct scrapes, tabular queries, system status, and exports.
* **📥 One-Click CSV Exporters**: Integrated file generators to export structured tabular data instantly to browser or CLI directory.
* **⚙️ Automated Scheduler**: Multi-threaded periodic scraper polling every 15 minutes, running silently as a daemon.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.14, Flask, SQLite3, BeautifulSoup4, Requests
* **Frontend**: HTML5, Responsive Vanilla CSS, JavaScript (ES6+), Chart.js
* **Automation**: Python Multi-threading & Daemons

---

## 📂 Directory Structure

```text
Automated-News-Web-Scraper/
├── app.py              # Flask server and API REST endpoints
├── database.py         # SQLite connection, relational schema, and keyword analytics
├── scraper.py          # Extensible BeautifulSoup4 scrapers (Hacker News & BBC Tech)
├── scheduler.py        # Background periodic scraping thread
├── cli.py              # Command Line Interface (CLI) tool
├── requirements.txt    # Python dependencies
├── .gitignore          # Repository ignored files (DB, caches, logs)
├── static/
│   ├── css/
│   │   └── style.css   # Main glassmorphism cyberpunk design
│   └── js/
│       └── app.js      # Frontend rendering logic and Chart.js integrations
├── templates/
│   └── index.html      # Glassmorphic web panel view
└── data/
    └── scraper.db      # SQLite database file (locally generated)
```

---

## 🚀 Installation & Running

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/lokireddy32457-bit/Automated-News-Web-Scraper.git
cd Automated-News-Web-Scraper
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Web Server & Dashboard
```bash
python app.py
```
* The web server will start on **`http://localhost:5000`**.
* The automated background scheduler daemon boots automatically and scrapes initial feeds.

---

## 💻 CLI Commands Usage

The application includes `cli.py` to control operations directly from your terminal:

* **Stats & Diagnostics Log**:
  ```bash
  python cli.py stats
  ```
* **List Stored Headlines (with filters)**:
  ```bash
  python cli.py list --limit 15 --source "Hacker News"
  ```
* **Trigger Immediate Real-Time Scrape**:
  ```bash
  python cli.py scrape
  ```
* **Export Entire Database to Local CSV**:
  ```bash
  python cli.py export metrics_export.csv
  ```
