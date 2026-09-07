# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_performance_collect_metrics"
# purpose: "Collect real-time CPU, RAM, Network I/O, Disk I/O, PostgreSQL & Redis metrics from staging Docker containers"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

import os
import sys
import time
import csv
import argparse
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


def get_docker_stats() -> List[Dict[str, str]]:
    """Fetches non-streaming docker container stats."""
    try:
        cmd = ["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
        lines = res.stdout.strip().splitlines()
        stats = []
        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                stats.append({
                    "name": parts[0],
                    "cpu_perc": parts[1],
                    "mem_usage": parts[2],
                    "net_io": parts[3],
                    "block_io": parts[4],
                })
        return stats
    except Exception as exc:
        print(f"[WARN] Failed to get docker stats: {exc}", file=sys.stderr)
        return []


def get_postgres_connections() -> int:
    """Queries active connections count from dnk_postgres container."""
    try:
        cmd = [
            "docker", "exec", "dnk_postgres",
            "psql", "-U", "dnk", "-d", "dnk_os", "-t", "-A",
            "-c", "SELECT count(*) FROM pg_stat_activity;"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
        return int(res.stdout.strip())
    except Exception:
        return -1


def get_redis_clients() -> int:
    """Queries connected clients count from dnk_redis container."""
    try:
        cmd = ["docker", "exec", "dnk_redis", "redis-cli", "info", "clients"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
        for line in res.stdout.splitlines():
            if line.startswith("connected_clients:"):
                return int(line.split(":")[1].strip())
        return -1
    except Exception:
        return -1


def collect_snapshot(csv_writer, csv_file) -> None:
    """Collects a single snapshot and flushes to CSV."""
    ts = datetime.now(timezone.utc).isoformat()
    pg_conns = get_postgres_connections()
    redis_clients = get_redis_clients()
    stats = get_docker_stats()

    if not stats:
        csv_writer.writerow([ts, "none", "0.0%", "0B / 0B", "0B / 0B", "0B / 0B", pg_conns, redis_clients])
        csv_file.flush()
        return

    for s in stats:
        csv_writer.writerow([
            ts,
            s["name"],
            s["cpu_perc"],
            s["mem_usage"],
            s["net_io"],
            s["block_io"],
            pg_conns,
            redis_clients
        ])
    csv_file.flush()


def main():
    parser = argparse.ArgumentParser(description="Collect staging Docker container resource metrics")
    parser.add_argument("--output", default="docs/performance/metrics_staging_20260905.csv", help="CSV output destination")
    parser.add_argument("--interval", type=int, default=30, help="Sampling interval in seconds (default: 30)")
    parser.add_argument("--duration", type=int, default=0, help="Total monitoring duration in seconds (0 = snapshot/continuous)")
    parser.add_argument("--snapshot", action="store_true", help="Record a single snapshot and exit")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    file_exists = os.path.exists(args.output) and os.path.getsize(args.output) > 0

    with open(args.output, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "container", "cpu_perc", "mem_usage", "net_io", "block_io", "pg_connections", "redis_clients"
            ])
            f.flush()

        if args.snapshot:
            collect_snapshot(writer, f)
            print(f"[OK] Single snapshot collected to {args.output}")
            return

        start_time = time.time()
        print(f"[INFO] Monitoring started: interval={args.interval}s, output={args.output}")
        try:
            while True:
                collect_snapshot(writer, f)
                if args.duration > 0 and (time.time() - start_time) >= args.duration:
                    break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[INFO] Monitoring stopped by user.")


if __name__ == "__main__":
    main()
