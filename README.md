# iHack 2026 Finals — Attack & Defense Toolkit

Pre-competition automation and Blue Ops monitoring toolkit built strictly in compliance with iHack 2026 Final Round rules (zero AI/MCP bindings, `>= 2.2s` anti-DDoS request pacing, zero firewall modifications).

## Repository Structure
- `ad_runner.py` — Automated multi-team exploit loop & regex flag submitter.
- `blue_ops.sh` — Initial service/config snapshotter + rotating `tcpdump` PCAP logger.
- `watch_changes.py` — Real-time file integrity monitor to catch rival webshells or tampered files.
- `setup_pwnbox.sh` — Workspace folder setup inside the browser Pwnbox.

---

## Quick Start Inside Pwnbox / Target Box

### 1. Initialize Pwnbox Workspace (Run on your Pwnbox)
```bash
git clone <YOUR_REPO_URL> ~/ihack && cd ~/ihack
chmod +x *.sh *.py
./setup_pwnbox.sh