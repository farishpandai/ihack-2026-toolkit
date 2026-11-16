# iHack 2026 Finals — Attack & Defense Toolkit

Pre-competition automation and Blue Ops monitoring toolkit built strictly in compliance with iHack 2026 Final Round rules (zero AI/MCP bindings, `>= 2.0s` anti-DDoS request pacing, zero firewall modifications).

---

## Event Structure & Scoring Mechanics

- **Phase 1: Hack & Defense (Attack/Defense) — 12 Hours**
  - Runs immediately in Round 1. Both offense and defense scripts are needed from minute one.
  - **Scoring per Tick:**
    - **Unfixed Rival Vulnerabilities:** Every tick a rival team leaves a vulnerability unpatched, `ad_runner.py` harvests their rotated flag and scores Attack points continuously until they patch it.
    - **Unfixed Own Vulnerabilities:** Every tick your own team leaves a bug unpatched, rival teams drain your flag and deduct your Defense points.
    - **SLA / Uptime:** Never shut down a vulnerable service—patch the code and restart cleanly so you don't lose availability points.
- **Phase 2: Final Round — 12 Hours**
  - Format disclosed after Phase 1 concludes (substitute teammate swap can occur between Phase 1 and Phase 2).
- **Venue Reminder (Dewan Mawar Qaseh, UiTM Shah Alam):**
  - Centralized air conditioning is very cold—bring a thick jacket/hoodie, pillow, multi-plug extension, PLANET managed switch + C13 power cable, 4 Ethernet cables, and ensure your laptop Ethernet IPv4 is set to **Automatic (DHCP)**.

---

## Repository Structure (All 10 Files)

### 1. `config.yaml`
Shared configuration read by `ad_runner.py`, `service_healthcheck.py`, `watch_changes.py`, `log_watch.sh`, and `alert_notify.sh` so you fill in real values once during briefing instead of editing source code under pressure:
- `team_id` & `team_token`
- `num_teams`, `ip_template`, `flag_regex`, `submit_url`, `request_delay` (`>= 2.2s`), and `tick_interval`
- `services` (your own `127.0.0.1` ports/HTTP paths for SLA monitoring)
- `log_paths` (Nginx, Apache, and auth logs to monitor)
- `alert_webhook_url` (optional Discord/Slack incoming webhook)

### 2. `ad_runner.py`
Automated Attack/Defense exploit-and-submit loop, run from your **Pwnbox** against every other team's box.
- Builds `TARGETS` dynamically from `ip_template` x `num_teams` in `config.yaml`, automatically excluding your own `team_id`.
- Calls `exploit(target_ip)` on each target, extracts flags via `flag_regex`, and POSTs new flags to `submit_url` with `X-Team-Token`.
- **Anti-DDoS Safety Lock:** Refuses to start if `request_delay < 2.0` seconds, and paces full cycles to `tick_interval`.
- **Crash-Safe Deduplication:** Persists submitted flags to `submitted_flags.json` on disk so restarts mid-round never lose state or resubmit duplicate flags.

### 3. `blue_ops.sh`
One-shot defensive snapshot + traffic capture, run immediately upon getting shell access to your own **Team Vulnbox**.
- Creates a timestamped, `chmod 700` backup (`/root/.sys_bak_HHMM`) of `/var/www`, `/opt`, `/srv`, `/etc/nginx`, `/etc/apache2`, and `/etc/systemd/system`.
- Saves initial listening ports (`ss -tulpn`) and running processes (`ps auxf`) inside the backup directory.
- Starts a background rotating `tcpdump` capture (`-i any`, 50MB chunks, max 10 files) at `/root/.pcaps/capture.pcap` for forensic inspection of rival payloads.

### 4. `watch_changes.py`
Real-time file-integrity monitor that polls `/var/www`, `/opt`, and `/srv` every 5 seconds.
- Alerts on `[ALERT - NEW FILE]` (dropped webshells), `[ALERT - MODIFIED]`, and `[ALERT - DELETED]`, forwarding alerts to `alert_webhook_url` if set in `config.yaml`.

### 5. `persistence_check.sh`
Detects attacker persistence outside web/app directories (`watch_changes.py` only hashes `/var/www`, `/opt`, `/srv`).
- `./persistence_check.sh baseline` snapshots cron jobs, SSH `authorized_keys`, SUID/SGID binaries, enabled systemd units, and shell-capable accounts in `/etc/passwd`.
- `./persistence_check.sh check` diffs current state against the baseline to flag unauthorized backdoors.

### 6. `service_healthcheck.py`
Polls your own exposed services (`127.0.0.1`, configured under `services:` in `config.yaml`) every 15 seconds via TCP connect or HTTP GET (`status < 500`), alerting on `[DOWN]` and `[RECOVERED]` so a crashed service or bad patch never silently drains SLA points.

### 7. `log_watch.sh`
Tails the `log_paths` configured in `config.yaml` in real time and greps for exploit/webshell signatures (`cmd=`, `eval(`, `base64_decode(`, `passthru(`, `shell_exec(`, `system(`, `../`, `union select`, reverse shells, etc.), alerting immediately via stdout and webhook.

### 8. `patch_restore.sh`
Fast rollback of tampered files from `blue_ops.sh` backups:
- `./patch_restore.sh list` — lists available `/root/.sys_bak_*` snapshots.
- `./patch_restore.sh restore <backup_dir> <path>` — quarantines the current tampered file into `/root/.quarantine_HHMMSS` for forensics, then restores the clean backup copy in place.

### 9. `alert_notify.sh`
Shared alert helper sourced by `log_watch.sh` (`alert "message"` prints a timestamped line and POSTs to `alert_webhook_url` in `config.yaml` if configured).

### 10. `setup_pwnbox.sh`
Workspace bootstrap for a fresh browser **Pwnbox**: creates `~/ihack/{web,pwn,rev,crypto,forensics,scripts}`, downloads Burp Suite Community Edition JAR, and adds a `burp` launcher alias to `~/.bashrc`.

---

## Morning Deployment Checklist

### Step 1: Clone, Fix Windows CRLF Line Endings & Check PyYAML (CRITICAL!)
Because this repository was pushed from Windows, run `sed` immediately after cloning so Linux does not throw `/bin/bash^M: bad interpreter`:

    git clone [https://github.com/farishpandai/ihack-2026-toolkit.git](https://github.com/farishpandai/ihack-2026-toolkit.git) ~/ihack && cd ~/ihack
    sed -i 's/\r$//' *.sh *.py
    chmod +x *.sh *.py
    python3 -c "import yaml" 2>/dev/null || pip install pyyaml

### Step 2: Initialize Your Browser Pwnbox

    ./setup_pwnbox.sh

*(Fast Web Tip: Use Firefox DevTools `F12 -> Network -> Right-click -> Copy as cURL` and convert to Python `requests` for rapid exploit prototyping.)*

### Step 3: Lock Down & Monitor Your Team Vulnbox

    sudo ./blue_ops.sh
    sudo ./persistence_check.sh baseline
    tmux new -s defense
    # Pane 1: python3 watch_changes.py
    # Pane 2: ./log_watch.sh
    # Pane 3: python3 service_healthcheck.py

### Step 4: Configure & Launch Automated Flag Harvester (On Pwnbox)
1. Fill in `team_id`, `team_token`, `ip_template`, `flag_regex`, `submit_url`, and `services` inside `config.yaml`.
2. **OPSEC RULE:** Never `git push` real `team_token`, `alert_webhook_url`, or live exploits back to a Public GitHub repository (flip the repo to **Private** first if pushing updates).
3. Implement `exploit(target_ip)` inside `ad_runner.py` and launch inside `tmux`:

    tmux new -s attack "python3 ad_runner.py"

---

## Incident Response Quick Commands (During Match)

- **Inspect captured rival HTTP traffic:**

      tshark -r /root/.pcaps/capture.pcap -Y "http.request"

- **Check for hidden backdoors (cron, SSH keys, new users, SUID):**

      sudo ./persistence_check.sh check

- **Quarantine & rollback a tampered web file:**

      sudo ./patch_restore.sh list
      sudo ./patch_restore.sh restore /root/.sys_bak_HHMM /var/www/html/index.php

---

## Hard Rules Reminder (Zero Tolerance)
- **NO AI** during the match (no ChatGPT, Claude, Gemini, Copilot, or MCP agents).
- **NO Firewall Edits** (`iptables`, `ufw`, `nftables` IP blocking is strictly forbidden).
- **NO Port/Dir Scanning** (`nmap`, `masscan`, `ffuf`, `gobuster` against rival teams is banned).
- **Rate Limit:** Keep `request_delay >= 2.0` seconds in `config.yaml`.
- **Preserve SLA:** Never shut down a vulnerable service—patch the code and restart cleanly.
