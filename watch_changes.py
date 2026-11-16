#!/usr/bin/env python3
import os
import time
import hashlib

WATCH_DIRS = ["/var/www", "/opt", "/srv"]

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
            print(f"[ALERT - NEW FILE] {path}")
        elif baseline[path] != h:
            print(f"[ALERT - MODIFIED] {path}")
    for path in set(baseline) - set(current):
        print(f"[ALERT - DELETED]  {path}")
    baseline = current