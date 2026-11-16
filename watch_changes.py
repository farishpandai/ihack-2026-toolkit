#!/usr/bin/env python3
"""
Real-time file-integrity monitor for /var/www, /opt, /srv. Now also POSTs
alerts to the webhook in config.yaml (if set), so a new/modified/deleted file
doesn't go unnoticed when nobody's watching the terminal at 4am.
"""
import os
import time
import hashlib
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    import requests
except ImportError:
    requests = None

WATCH_DIRS = ["/var/www", "/opt", "/srv"]

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"

WEBHOOK_URL = ""
if yaml is not None and CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH) as f:
            WEBHOOK_URL = (yaml.safe_load(f) or {}).get("alert_webhook_url", "") or ""
    except Exception:
        pass


def alert(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    if WEBHOOK_URL and requests is not None:
        try:
            requests.post(WEBHOOK_URL, json={"content": f"[{ts}] {msg}"}, timeout=3)
        except Exception:
            pass  # best-effort; never let a failed webhook kill the monitor


def snapshot():
    state = {}
    for base in WATCH_DIRS:
        if not os.path.exists(base):
            continue
        for root, _, files in os.walk(base):
            for f in files:
                path = os.path.join(root, f)
                try:
                    with open(path, "rb") as fp:
                        state[path] = hashlib.md5(fp.read()).hexdigest()
                except Exception:
                    pass
    return state


baseline = snapshot()
print(f"[*] Watching {len(baseline)} files for unauthorized changes/webshells...")

while True:
    time.sleep(5)
    current = snapshot()
    for path, h in current.items():
        if path not in baseline:
            alert(f"[ALERT - NEW FILE] {path}")
        elif baseline[path] != h:
            alert(f"[ALERT - MODIFIED] {path}")
    for path in set(baseline) - set(current):
        alert(f"[ALERT - DELETED]  {path}")
    baseline = current
