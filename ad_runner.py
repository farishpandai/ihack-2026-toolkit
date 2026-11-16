#!/usr/bin/env python3
import re
import time
import requests

# --- CONFIGURATION (Fill in during briefing) ---
TARGETS = [f"10.10.{i}.1" for i in range(1, 31) if i != 99]  # Exclude your own team ID!
FLAG_REGEX = r"IHACK\{[a-zA-Z0-9_\-]+\}"                     # Update flag format on event day
SUBMIT_URL = "http://10.10.0.1/api/flags"                    # Update scoreboard API endpoint
TEAM_TOKEN = "YOUR_TEAM_TOKEN_HERE"
TICK_INTERVAL = 60                                           # Seconds between full rounds
REQUEST_DELAY = 2.2                                          # STRICT RULE: >= 2s delay!

submitted_flags = set()

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
    except Exception as e:
        print(f"[-] Flag submit error for {flag}: {e}")

def main():
    print(f"[*] Starting A/D runner against {len(TARGETS)} targets (delay={REQUEST_DELAY}s)...")
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