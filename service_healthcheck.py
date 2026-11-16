#!/usr/bin/env python3
"""
Polls your own exposed services (from config.yaml) on a timer and alerts when
one goes down. Many A/D scoreboards dock points for YOUR OWN downtime
separately from getting exploited, so this is about catching a crashed
service or a bad patch before it costs you SLA points — not about probing
other teams (that's against the rules).

Usage: ./service_healthcheck.py [--interval SECONDS]
"""
import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    import requests
except ImportError:
    requests = None

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_config():
    if yaml is None:
        print("[!] PyYAML not installed; install it or hardcode SERVICES below.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def alert(msg: str, webhook_url: str = ""):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    if webhook_url and requests is not None:
        try:
            requests.post(webhook_url, json={"content": f"[{ts}] {msg}"}, timeout=3)
        except Exception:
            pass  # best-effort; don't let a failed alert crash the checker


def check_tcp(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_http(host: str, port: int, path: str, timeout: float = 3.0) -> bool:
    if requests is None:
        return check_tcp(host, port, timeout)
    url = f"http://{host}:{port}{path}"
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=15.0, help="seconds between checks")
    args = parser.parse_args()

    cfg = load_config()
    services = cfg.get("services", [])
    webhook_url = cfg.get("alert_webhook_url", "") or ""

    if not services:
        print("[!] No services defined in config.yaml — add them under `services:` first.")
        sys.exit(1)

    print(f"[*] Health-checking {len(services)} service(s) every {args.interval}s...")
    state = {s["name"]: True for s in services}  # assume up at start

    while True:
        for svc in services:
            name = svc["name"]
            host = svc.get("host", "127.0.0.1")
            port = svc["port"]
            path = svc.get("http_path")

            up = check_http(host, port, path) if path else check_tcp(host, port)

            if up and not state[name]:
                alert(f"[RECOVERED] {name} ({host}:{port}) is back up", webhook_url)
            elif not up and state[name]:
                alert(f"[DOWN] {name} ({host}:{port}) failed health check!", webhook_url)

            state[name] = up

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
