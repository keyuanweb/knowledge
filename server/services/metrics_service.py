"""
简易进程内指标（Prometheus text），便于客户对接 Grafana。
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict

_lock = threading.Lock()
_counters: dict[str, int] = defaultdict(int)
_errors: dict[str, int] = defaultdict(int)
_lat_sum_ms: dict[str, float] = defaultdict(float)
_lat_count: dict[str, int] = defaultdict(int)


def inc_counter(name: str, n: int = 1) -> None:
    with _lock:
        _counters[name] += n


def inc_error(name: str, n: int = 1) -> None:
    with _lock:
        _errors[name] += n


def observe_latency(route_key: str, elapsed_ms: float) -> None:
    with _lock:
        _lat_sum_ms[route_key] += elapsed_ms
        _lat_count[route_key] += 1


def prometheus_text() -> str:
    lines: list[str] = []
    lines.append("# HELP http_requests_total API 请求计数")
    lines.append("# TYPE http_requests_total counter")
    with _lock:
        now = int(time.time() * 1000)
        for k, v in sorted(_counters.items()):
            lines.append(f'http_requests_total{{route="{k}"}} {v}')
        lines.append("# HELP http_errors_total API 错误计数")
        lines.append("# TYPE http_errors_total counter")
        for k, v in sorted(_errors.items()):
            lines.append(f'http_errors_total{{route="{k}"}} {v}')
        lines.append("# HELP http_request_duration_ms_sum 累计耗时毫秒")
        lines.append("# TYPE http_request_duration_ms_sum counter")
        for k in sorted(set(_lat_sum_ms.keys()) | set(_lat_count.keys())):
            s = _lat_sum_ms.get(k, 0.0)
            lines.append(f'http_request_duration_ms_sum{{route="{k}"}} {s}')
        lines.append(f"enterprise_qa_metrics_generated_ms {now}")
    return "\n".join(lines) + "\n"
