import threading
import time
import scraper

class ScrapeScheduler:
    """
    A robust background worker that schedules and triggers news scraping tasks
    periodically using a daemon thread.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ScrapeScheduler, cls).__new__(cls)
                cls._instance._init_scheduler()
            return cls._instance

    def _init_scheduler(self):
        self.interval = 1800  # Default 30 minutes in seconds
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.last_run_time = None

    def start(self, interval_seconds=1800):
        """Starts the background scheduler thread if not already running."""
        with self._lock:
            if self.running:
                print("[Scheduler] Already running.")
                return False
            
            self.interval = interval_seconds
            self.running = True
            self.stop_event.clear()
            
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print(f"[Scheduler] Background daemon started with interval: {self.interval}s")
            return True

    def stop(self):
        """Gracefully halts the background scheduler thread."""
        with self._lock:
            if not self.running:
                print("[Scheduler] Already stopped.")
                return False
                
            self.running = False
            self.stop_event.set()
            print("[Scheduler] Stop signal sent to background daemon.")
            return True

    def set_interval(self, interval_seconds):
        """Changes the polling frequency on the fly."""
        with self._lock:
            self.interval = interval_seconds
            print(f"[Scheduler] Polling interval updated to: {self.interval}s")

    def _run_loop(self):
        """Internal main loop of the background thread."""
        print("[Scheduler] Worker loop initialized.")
        
        # Immediate run on start to gather initial data
        try:
            self.last_run_time = time.time()
            scraper.run_all_scrapers()
        except Exception as e:
            print(f"[Scheduler] Initial run failed: {e}")
            
        while not self.stop_event.is_set():
            # Perform sleep in small increments to respond quickly to stop signals
            sleep_chunks = int(self.interval)
            for _ in range(sleep_chunks):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
                
            if self.stop_event.is_set():
                break
                
            print("[Scheduler] Periodic trigger activated...")
            try:
                self.last_run_time = time.time()
                scraper.run_all_scrapers()
            except Exception as e:
                print(f"[Scheduler] Periodic scrape task execution failed: {e}")
                
        print("[Scheduler] Worker loop terminated.")

# Global singleton instance
scheduler_instance = ScrapeScheduler()
