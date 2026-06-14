import threading
from typing import Dict, List, Tuple
from fastapi import APIRouter, Response

router = APIRouter(tags=["Metrics"])

class MetricsCollector:
    """Thread-safe singleton metrics collector formatting records for Prometheus integration."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "MetricsCollector":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_metrics()
            return cls._instance

    def _init_metrics(self) -> None:
        self.request_counts: Dict[Tuple[str, str, str], int] = {}
        self.request_durations: Dict[Tuple[str, str], List[float]] = {}
        self.task_counts: Dict[Tuple[str, str], int] = {}
        self.db_durations: List[float] = []
        self.search_durations: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def record_request(self, method: str, path: str, status: int, duration: float) -> None:
        """Log details of a request execution."""
        with self.lock:
            key = (method, path, str(status))
            self.request_counts[key] = self.request_counts.get(key, 0) + 1
            
            dur_key = (method, path)
            dur_list = self.request_durations.get(dur_key, [])
            dur_list.append(duration)
            self.request_durations[dur_key] = dur_list[-100:] # Keep rolling window of last 100

    def record_task(self, name: str, status: str) -> None:
        """Log details of Celery task completions."""
        with self.lock:
            key = (name, status)
            self.task_counts[key] = self.task_counts.get(key, 0) + 1

    def record_db(self, duration: float) -> None:
        """Log database engine query duration metrics."""
        with self.lock:
            self.db_durations.append(duration)
            self.db_durations = self.db_durations[-100:]

    def record_search(self, mode: str, duration: float) -> None:
        """Log search engine execution latency metrics."""
        with self.lock:
            dur_list = self.search_durations.get(mode, [])
            dur_list.append(duration)
            self.search_durations[mode] = dur_list[-100:]

    def get_prometheus_output(self) -> str:
        """Retrieve plain-text metrics representation structured for Prometheus ingestion."""
        with self.lock:
            lines = []
            
            # 1. Requests Count
            lines.append("# HELP http_requests_total Total number of HTTP requests processed.")
            lines.append("# TYPE http_requests_total counter")
            for (method, path, status_code), count in self.request_counts.items():
                lines.append(f'http_requests_total{{method="{method}",path="{path}",status="{status_code}"}} {count}')
                
            # 2. Average Request Durations
            lines.append("# HELP http_request_duration_seconds_avg Average duration of HTTP requests in seconds.")
            lines.append("# TYPE http_request_duration_seconds_avg gauge")
            for (method, path), durations in self.request_durations.items():
                avg = sum(durations) / len(durations) if durations else 0.0
                lines.append(f'http_request_duration_seconds_avg{{method="{method}",path="{path}"}} {avg:.4f}')

            # 3. Task Completions
            lines.append("# HELP celery_tasks_total Total Celery background tasks processed.")
            lines.append("# TYPE celery_tasks_total counter")
            for (name, task_status), count in self.task_counts.items():
                lines.append(f'celery_tasks_total{{name="{name}",status="{task_status}"}} {count}')

            # 4. DB Latencies
            lines.append("# HELP db_query_duration_seconds_avg Average query processing duration in seconds.")
            lines.append("# TYPE db_query_duration_seconds_avg gauge")
            avg_db = sum(self.db_durations) / len(self.db_durations) if self.db_durations else 0.0
            lines.append(f"db_query_duration_seconds_avg {avg_db:.4f}")

            # 5. Search Latencies
            lines.append("# HELP search_latency_seconds_avg Average search query latency in seconds.")
            lines.append("# TYPE search_latency_seconds_avg gauge")
            for mode, durations in self.search_durations.items():
                avg_search = sum(durations) / len(durations) if durations else 0.0
                lines.append(f'search_latency_seconds_avg{{mode="{mode}"}} {avg_search:.4f}')

            return "\n".join(lines) + "\n"

metrics_collector = MetricsCollector()

@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """Prometheus endpoints exposing telemetry metrics details."""
    output = metrics_collector.get_prometheus_output()
    return Response(content=output, media_type="text/plain")
