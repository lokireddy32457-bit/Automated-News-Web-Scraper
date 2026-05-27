// Global State variables
let currentPage = 1;
const limit = 12;
let totalArticles = 0;
let searchQuery = "";
let sourceFilter = "";

// Chart instances
let trendChart = null;
let sourceChart = null;
let keywordChart = null;

// DOM Elements
const elements = {
    totalArticles: document.getElementById("stat-total-articles"),
    hnArticles: document.getElementById("stat-hn-articles"),
    bbcArticles: document.getElementById("stat-bbc-articles"),
    lastScrape: document.getElementById("stat-last-scrape"),
    btnManualScrape: document.getElementById("btn-manual-scrape"),
    btnExportCsv: document.getElementById("btn-export-csv"),
    searchInput: document.getElementById("search-input"),
    sourceFilter: document.getElementById("source-filter"),
    articlesBody: document.getElementById("articles-body"),
    paginationSummary: document.getElementById("pagination-summary"),
    btnPrevPage: document.getElementById("btn-prev-page"),
    btnNextPage: document.getElementById("btn-next-page"),
    logsToggle: document.getElementById("logs-toggle"),
    logsBody: document.getElementById("logs-body"),
    logsList: document.getElementById("logs-list"),
    toast: document.getElementById("toast")
};

// Main Initialization
document.addEventListener("DOMContentLoaded", () => {
    initEventListeners();
    loadDashboardData();
});

// Event Listeners Registration
function initEventListeners() {
    // Manual trigger button
    elements.btnManualScrape.addEventListener("click", triggerManualScrape);
    
    // Search input (with 250ms debounce)
    let searchTimeout;
    elements.searchInput.addEventListener("input", (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchQuery = e.target.value;
            currentPage = 1;
            fetchArticles();
        }, 250);
    });

    // Source Filter dropdown
    elements.sourceFilter.addEventListener("change", (e) => {
        sourceFilter = e.target.value;
        currentPage = 1;
        fetchArticles();
    });

    // Export CSV Button
    elements.btnExportCsv.addEventListener("click", () => {
        const url = `/api/export?q=${encodeURIComponent(searchQuery)}&source=${encodeURIComponent(sourceFilter)}`;
        window.location.href = url;
        showToast("Generating custom CSV export report...", "info");
    });

    // Pagination actions
    elements.btnPrevPage.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            fetchArticles();
        }
    });

    elements.btnNextPage.addEventListener("click", () => {
        const maxPage = Math.ceil(totalArticles / limit);
        if (currentPage < maxPage) {
            currentPage++;
            fetchArticles();
        }
    });

    // Toggle logs panel drawer
    elements.logsToggle.addEventListener("click", () => {
        elements.logsBody.classList.toggle("collapsed");
        const toggleIcon = elements.logsToggle.querySelector(".toggle-icon");
        if (elements.logsBody.classList.contains("collapsed")) {
            toggleIcon.innerText = "▼";
        } else {
            toggleIcon.innerText = "▲";
        }
    });
}

// Master Fetch and Refresh
async function loadDashboardData() {
    await fetchAnalytics();
    await fetchArticles();
}

// 1. Fetch Analytics & Metrics
async function fetchAnalytics() {
    try {
        const response = await fetch("/api/analytics");
        const res = await response.json();
        
        if (res.success) {
            const data = res.analytics;
            
            // Populate Metrics
            elements.totalArticles.innerText = data.total_count.toLocaleString();
            
            // Get source breakdowns
            const hnCount = data.sources.find(s => s.source === "Hacker News")?.count || 0;
            const bbcCount = data.sources.find(s => s.source === "BBC Tech")?.count || 0;
            
            elements.hnArticles.innerText = hnCount.toLocaleString();
            elements.bbcArticles.innerText = bbcCount.toLocaleString();
            
            // Set last scrape time from recent success logs
            if (res.logs && res.logs.length > 0) {
                const recentSuccess = res.logs.find(l => l.status === "SUCCESS");
                if (recentSuccess) {
                    elements.lastScrape.innerText = formatRelativeTime(recentSuccess.timestamp);
                }
            }
            
            // Render Chart.js Visualizations
            renderTrendsChart(data.daily_volumes);
            renderSourceDistributionChart(hnCount, bbcCount);
            renderKeywordsChart(data.keywords);
            
            // Populate Diagnostics Logs
            populateLogs(res.logs);
        }
    } catch (err) {
        console.error("Error fetching analytics:", err);
        showToast("Error updating analytics dashboard panels.", "error");
    }
}

// 2. Fetch Article Tabular Grid Data
async function fetchArticles() {
    const offset = (currentPage - 1) * limit;
    const url = `/api/articles?q=${encodeURIComponent(searchQuery)}&source=${encodeURIComponent(sourceFilter)}&limit=${limit}&offset=${offset}`;
    
    try {
        const response = await fetch(url);
        const res = await response.json();
        
        if (res.success) {
            totalArticles = res.total;
            populateArticlesTable(res.articles);
            updatePaginationUI();
        }
    } catch (err) {
        console.error("Error fetching articles:", err);
        showToast("Error retrieving structured news headlines.", "error");
    }
}

// Populate grid table contents
function populateArticlesTable(articles) {
    if (!articles || articles.length === 0) {
        elements.articlesBody.innerHTML = `
            <tr>
                <td colspan="5" class="table-placeholder">No articles match current filters or search terms.</td>
            </tr>
        `;
        return;
    }
    
    elements.articlesBody.innerHTML = "";
    
    articles.forEach((art, index) => {
        const overallIndex = (currentPage - 1) * limit + index + 1;
        
        // Define clean source labels
        const sourceBadge = art.source === "Hacker News" 
            ? `<span class="badge badge-hn">Hacker News</span>` 
            : `<span class="badge badge-bbc">BBC Tech</span>`;
            
        // Style specific categories
        let categoryClass = "badge-category";
        const cat = (art.category || "General").toLowerCase();
        if (cat.includes("ai") || cat.includes("ml")) {
            categoryClass += " badge-cat-ai";
        } else if (cat.includes("cyber") || cat.includes("security")) {
            categoryClass += " badge-cat-cyber";
        } else if (cat.includes("gadget") || cat.includes("device") || cat.includes("phone")) {
            categoryClass += " badge-cat-gadgets";
        } else if (cat.includes("game") || cat.includes("console") || cat.includes("gaming")) {
            categoryClass += " badge-cat-gaming";
        }
        
        const categoryBadge = `<span class="badge ${categoryClass}">${art.category || "General"}</span>`;
        
        // Pretty format timestamp
        const timeDisplay = art.scraped_at ? formatTimeStr(art.scraped_at) : "-";
        
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><span class="time-stamp">${overallIndex}</span></td>
            <td>
                <a href="${art.url}" target="_blank" rel="noopener noreferrer" class="article-link">
                    ${escapeHtml(art.title)}
                </a>
            </td>
            <td>${sourceBadge}</td>
            <td>${categoryBadge}</td>
            <td><span class="time-stamp">${timeDisplay}</span></td>
        `;
        elements.articlesBody.appendChild(row);
    });
}

// Update Pagination button states
function updatePaginationUI() {
    const totalPages = Math.ceil(totalArticles / limit) || 1;
    
    const start = (currentPage - 1) * limit + 1;
    const end = Math.min(currentPage * limit, totalArticles);
    
    if (totalArticles === 0) {
        elements.paginationSummary.innerText = "Showing 0 entries";
    } else {
        elements.paginationSummary.innerText = `Showing ${start}-${end} of ${totalArticles.toLocaleString()} entries`;
    }
    
    elements.btnPrevPage.disabled = currentPage === 1;
    elements.btnNextPage.disabled = currentPage >= totalPages;
}

// Trigger real-time Scraping Process
async function triggerManualScrape() {
    // Add visual loading triggers
    elements.btnManualScrape.classList.add("spinning");
    elements.btnManualScrape.disabled = true;
    
    showToast("Launching active web scrapers. Fetching real-time headlines...", "info");
    
    try {
        const response = await fetch("/api/scrape", { method: "POST" });
        const res = await response.json();
        
        if (res.success) {
            showToast(`Harvest complete! Discovered ${res.articles_scraped} new headlines.`, "success");
            // Refresh data immediately
            currentPage = 1;
            await loadDashboardData();
        } else {
            showToast("Manual scraping failed. Check diagnostics logs below.", "error");
        }
    } catch (err) {
        console.error("Error triggering manual scrape:", err);
        showToast("Network failure. Scrapers unreachable.", "error");
    } finally {
        // Halt loading indicators
        elements.btnManualScrape.classList.remove("spinning");
        elements.btnManualScrape.disabled = false;
    }
}

// Render Daily Scrape volumes (Line chart)
function renderTrendsChart(volumes) {
    const ctx = document.getElementById("chart-trends").getContext("2d");
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    const labels = volumes.map(v => {
        // Format to brief MM/DD style
        const parts = v.date.split('-');
        return parts.length > 2 ? `${parts[1]}/${parts[2]}` : v.date;
    });
    const dataPoints = volumes.map(v => v.count);
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Headlines Scraped',
                data: dataPoints,
                borderColor: '#d946ef',
                borderWidth: 3,
                backgroundColor: 'rgba(217, 70, 239, 0.15)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#10b981',
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(15, 23, 42, 0.05)' },
                    ticks: { color: '#475569' }
                },
                y: {
                    grid: { color: 'rgba(15, 23, 42, 0.05)' },
                    ticks: { color: '#475569', precision: 0 }
                }
            }
        }
    });
}

// Render Feed Distribution (Doughnut Chart)
function renderSourceDistributionChart(hn, bbc) {
    const ctx = document.getElementById("chart-sources").getContext("2d");
    
    if (sourceChart) {
        sourceChart.destroy();
    }
    
    sourceChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Hacker News', 'BBC Tech'],
            datasets: [{
                data: [hn, bbc],
                backgroundColor: ['#ff9f1c', '#8b5cf6'],
                borderColor: 'rgba(255, 255, 255, 0.8)',
                borderWidth: 2,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#0f172a', font: { family: 'Inter', size: 11 } }
                }
            },
            cutout: '65%'
        }
    });
}

// Render Keywords frequency counts (Horizontal Bar Chart)
function renderKeywordsChart(keywords) {
    const ctx = document.getElementById("chart-keywords").getContext("2d");
    
    if (keywordChart) {
        keywordChart.destroy();
    }
    
    const labels = keywords.map(k => k.word);
    const counts = keywords.map(k => k.count);
    
    keywordChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Occurrences',
                data: counts,
                backgroundColor: 'rgba(16, 185, 129, 0.7)',
                borderColor: '#10b981',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(15, 23, 42, 0.05)' },
                    ticks: { color: '#475569', precision: 0 }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#0f172a', font: { family: 'Outfit', weight: '500' } }
                }
            }
        }
    });
}

// Populate Diagnostic log rows
function populateLogs(logs) {
    if (!logs || logs.length === 0) {
        elements.logsList.innerHTML = `<div class="log-row">No runs recorded. Trigger scrape to establish log database.</div>`;
        return;
    }
    
    elements.logsList.innerHTML = "";
    
    logs.forEach(log => {
        const timeStr = log.timestamp.replace("T", " ").substring(0, 19);
        const statusClass = log.status === "SUCCESS" ? "log-status-success" : "log-status-failed";
        const errMsg = log.error_message || "-";
        
        const row = document.createElement("div");
        row.className = "log-row";
        row.innerHTML = `
            <span>${timeStr}</span>
            <span>${escapeHtml(log.source)}</span>
            <span class="${statusClass}">${log.status}</span>
            <span>${log.articles_scraped}</span>
            <span>${escapeHtml(errMsg)}</span>
        `;
        elements.logsList.appendChild(row);
    });
}

// Helper: Toast Notifications
function showToast(message, type = "info") {
    elements.toast.innerText = message;
    elements.toast.className = "toast"; // Reset
    
    if (type === "success") {
        elements.toast.style.borderColor = "#10b981";
        elements.toast.style.boxShadow = "0 10px 25px rgba(16, 185, 129, 0.3)";
    } else if (type === "error") {
        elements.toast.style.borderColor = "#f43f5e";
        elements.toast.style.boxShadow = "0 10px 25px rgba(244, 63, 94, 0.3)";
    } else {
        elements.toast.style.borderColor = "#d946ef";
        elements.toast.style.boxShadow = "0 10px 25px rgba(217, 70, 239, 0.3)";
    }
    
    elements.toast.classList.remove("hidden");
    
    // Hide toast after 4.5 seconds
    setTimeout(() => {
        elements.toast.classList.add("hidden");
    }, 4500);
}

// Utility: Relative Date/Time formatter
function formatRelativeTime(isoString) {
    try {
        const parsed = new Date(isoString);
        const diffMs = new Date() - parsed;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return "Just Now";
        if (diffMins < 60) return `${diffMins}m ago`;
        
        const diffHrs = Math.floor(diffMins / 60);
        if (diffHrs < 24) return `${diffHrs}h ago`;
        
        return parsed.toLocaleDateString();
    } catch {
        return "Recently";
    }
}

// Utility: General pretty date/time string format
function formatTimeStr(isoString) {
    try {
        const parsed = new Date(isoString);
        return parsed.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
        return isoString;
    }
}

// Utility: Prevent XSS injection
function escapeHtml(text) {
    if (!text) return "";
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}
