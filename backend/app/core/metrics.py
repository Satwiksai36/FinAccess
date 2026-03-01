import threading
from typing import List

class MetricsCollector:
    def __init__(self, max_latency_history: int = 1000):
        self._lock = threading.Lock()
        
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        self._active_threads = 0
        self._ml_latency_history: List[float] = []
        self._latency_history: List[float] = []
        self._max_latency_history = max_latency_history
        
    def increment_requests(self):
        with self._lock:
            self.total_requests += 1
            
    def record_cache_hit(self):
        with self._lock:
            self.cache_hits += 1

    def record_cache_miss(self):
        with self._lock:
            self.cache_misses += 1
            
    def set_active_threads(self, count: int):
        with self._lock:
            self._active_threads = count

    def record_latency(self, latency_ms: float):
        with self._lock:
            self._latency_history.append(latency_ms)
            if len(self._latency_history) > self._max_latency_history:
                self._latency_history.pop(0)

    def record_ml_latency(self, latency_ms: float):
        with self._lock:
            self._ml_latency_history.append(latency_ms)
            if len(self._ml_latency_history) > self._max_latency_history:
                self._ml_latency_history.pop(0)

    def get_metrics(self) -> dict:
        with self._lock:
            history_copy = list(self._latency_history)
            ml_history_copy = list(self._ml_latency_history)
            
            avg_latency = 0.0
            p95_latency = 0.0
            avg_ml_latency = 0.0
            p95_ml_latency = 0.0
            
            if history_copy:
                avg_latency = sum(history_copy) / len(history_copy)
                
                # O(N log N) overhead mitigated by strictly bounding max history (1000 entries)
                # Ensure no massive memory leak blocks execution during get_metrics retrieval.
                sorted_hist = sorted(history_copy)
                p95_idx = int(0.95 * len(sorted_hist)) - 1
                p95_latency = sorted_hist[max(0, p95_idx)]
                
            if ml_history_copy:
                avg_ml_latency = sum(ml_history_copy) / len(ml_history_copy)
                sorted_ml_hist = sorted(ml_history_copy)
                p95_ml_idx = int(0.95 * len(sorted_ml_hist)) - 1
                p95_ml_latency = sorted_ml_hist[max(0, p95_ml_idx)]
                
            return {
                "total_requests": self.total_requests,
                "average_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "average_ml_latency_ms": round(avg_ml_latency, 2),
                "p95_ml_latency_ms": round(p95_ml_latency, 2),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "active_threads": self._active_threads
            }
