#!/usr/bin/env python3
"""
Automated multi-team exploit loop & flag submitter. Config (targets, flag
regex, submit URL, team token, delay) now lives in config.yaml — edit that at
briefing instead of this file.
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

try:
    import yaml
except ImportError:
    print("[!] PyYAML not installed (pip install pyyaml). Cannot load config.yaml.")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
SUBMITTED_FLAGS_PATH = SCRIPT_DIR / "submitted_flags.json"

with open(CONFIG_PATH) as f:
    CFG = yaml.safe_load(f)

_team_cfg = CFG["team"]
_comp_cfg = CFG["competition"]

MY_TEAM_ID = _team_cfg["team_id"]
TEAM_TOKEN = _team_cfg["team_token"]

TARGETS = [
    _comp_cfg["ip_template"].format(i)
    for i in range(1, _comp_cfg["num_teams"] + 1)
    if i != MY_TEAM_ID
]
FLAG_REGEX = _comp_cfg["flag_regex"]
SUBMIT_URL = _comp_cfg["submit_url"]
TICK_INTERVAL = _comp_cfg["tick_interval"]
REQUEST_DELAY = _comp_cfg["request_delay"]  # STRICT RULE: >= 2s delay!

if REQUEST_DELAY < 2.0:
    print(f"[!] request_delay in config.yaml is {REQUEST_DELAY}s — must be >= 2s per the rules. Refusing to start.")
    sys.exit(1)


def load_submitted_flags() -> set:
    """Load previously-submitted flags from disk so a restart doesn't lose dedup state."""
    if SUBMITTED_FLAGS_PATH.exists():
        try:
            return set(json.loads(SUBMITTED_FLAGS_PATH.read_text()))
        except Exception:
            return set()
    return set()


def save_submitted_flags(flags: set):
    try:
        SUBMITTED_FLAGS_PATH.write_text(json.dumps(sorted(flags)))
    except Exception as e:
        print(f"[!] Could not persist submitted flags: {e}")


submitted_flags = load_submitted_flags()


def exploit(target_ip: str) -> str:
    """
    Replace this body with your service exploit once you find the vuln.
    Must return raw response text containing the flag.
    """
    # Example placeholder:
    # r = requests.get(f"http://{target_ip}:8080/vuln?cmd=cat+/flag.txt", timeout=5)
    # return r.text
    return ""


def submit_flag(flag: str):
    if flag in submitted_flags:
        return
    try:
        # Adjust payload/headers to match the competition flag submission API
        res = requests.post(
            SUBMIT_URL,
            json={"flags": [flag]},
            headers={"X-Team-Token": TEAM_TOKEN},
            timeout=5
        )
        print(f"[+] Submitted {flag} -> {res.status_code}: {res.text.strip()}")
        submitted_flags.add(flag)
        save_submitted_flags(submitted_flags)
    except Exception as e:
        print(f"[-] Flag submit error for {flag}: {e}")


def main():
    print(f"[*] Starting A/D runner against {len(TARGETS)} targets (delay={REQUEST_DELAY}s)...")
    print(f"[*] Loaded {len(submitted_flags)} previously-submitted flag(s) from disk.")
    while True:
        round_start = time.time()
        for ip in TARGETS:
            try:
                output = exploit(ip)
                flags = re.findall(FLAG_REGEX, output)
                for flag in flags:
                    submit_flag(flag)
            except Exception as e:
                print(f"[!] Exploit failed on {ip}: {e}")

            # Mandatory anti-DDoS rule compliance
            time.sleep(REQUEST_DELAY)

        elapsed = time.time() - round_start
        sleep_left = max(1, TICK_INTERVAL - elapsed)
        print(f"[*] Cycle complete in {elapsed:.1f}s. Sleeping {sleep_left:.1f}s...")
        time.sleep(sleep_left)


if __name__ == "__main__":
    main()
