"""
CPU utilization and process thread profiler.
"""

import os
from typing import Dict, Any


def get_cpu_telemetry() -> Dict[str, Any]:
    """Collect process CPU utilization, thread counts, and core stats."""
    cpu_count = os.cpu_count() or 1
    cpu_percent = 0.0
    num_threads = 1

    try:
        import psutil
        proc = psutil.Process(os.getpid())
        cpu_percent = proc.cpu_percent(interval=0.1)
        num_threads = proc.num_threads()
    except Exception:
        pass

    return {
        "cpu_count": cpu_count,
        "cpu_percent": round(cpu_percent, 2),
        "num_threads": num_threads,
    }
