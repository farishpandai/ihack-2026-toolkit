# iHack 2026 Finals — Attack & Defense Toolkit

Pre-competition automation and Blue Ops monitoring toolkit built strictly in compliance with iHack 2026 Final Round rules (zero AI/MCP bindings, `>= 2.2s` anti-DDoS request pacing, zero firewall modifications).

## Repository Structure

### `config.yaml`
Shared configuration read by several scripts below, so you fill in real values once at briefing instead of editing source files under time pressure: your team ID/token, target IP template, flag regex, submit URL, request delay, your own exposed services (for health checks), log file locations (for log watching), and an optional alert webhook URL.

### `ad_runner.py`
Automated Attack/Defense exploit-and-submit loop, run from your own Pwnbox against every other team's box.
- Reads targets, flag regex, submit URL, team token, and timing from `config.yaml` (builds the `TARGETS` list from `ip_template` x `num_teams`, excluding your own `team_id`).
- On each round, calls `exploit(target_ip)` — a stub you implement per-service once you've found the vuln — against every target, extracts flags from the response with the configured flag regex, and POSTs each new flag to the submit URL with your team token.
- Enforces the competition's anti-DDoS rule by sleeping `request_delay` (refuses to start if it's set below 2.0s) between targets, and paces full rounds to `tick_interval`, sleeping out any remainder.
- Persists submitted flags to `submitted_flags.json` next to the script, so a crash/restart mid-round doesn't lose dedup state or risk resubmitting.

### `blue_ops.sh`
One-shot defensive snapshot + traffic capture, run right after you get shell access to your own team's A/D box.
- Creates a timestamped, `chmod 700` backup directory and copies `/var/www`, `/opt`, `/srv`, `/etc/nginx`, `/etc/apache2`, and `/etc/systemd/system` into it (skipping any that don't exist), so you have a known-good baseline to diff against or restore from.
- Dumps the current listening ports (`ss -tulpn`) and running processes (`ps auxf`) to text files in that same backup directory.
- Starts a backgrounded, rotating `tcpdump` capture (`-i any`, 50MB chunks, max 10 files) of all traffic on the box, for later forensic review of attacker activity.

### `watch_changes.py`
Real-time file-integrity monitor that polls `/var/www`, `/opt`, and `/srv` for signs of tampering.
- Takes an initial MD5 snapshot of every file under those directories, then re-scans every 5 seconds.
- Diffs each new scan against the previous one and alerts on any file that's new (`[ALERT - NEW FILE]`, e.g. a dropped webshell), changed (`[ALERT - MODIFIED]`), or removed (`[ALERT - DELETED]`).
- If `alert_webhook_url` is set in `config.yaml`, alerts are also posted there (Discord/Slack-compatible), not just printed to stdout.
- Runs indefinitely in the foreground — intended to be left running in a terminal/tmux pane throughout the competition.

### `persistence_check.sh`
Catches attacker persistence that `watch_changes.py` can't see, since it only hashes files under `/var/www`, `/opt`, `/srv`.
- `./persistence_check.sh baseline` snapshots cron jobs, SSH `authorized_keys` files, SUID/SGID binaries, enabled systemd units, and users with a login shell.
- `./persistence_check.sh check` re-snapshots and diffs against that baseline, flagging any new cron entry, authorized key, SUID binary, systemd unit, or shell-capable account.

### `service_healthcheck.py`
Polls your own exposed services (defined in `config.yaml`) on a timer and alerts on downtime — many A/D scoreboards penalize your own service outages separately from getting exploited, so this catches a crashed service or bad patch before it costs you SLA points.
- Does a plain TCP connect check, or an HTTP GET (status < 500 = healthy) when `http_path` is set for a service.
- Alerts (stdout + webhook) on `[DOWN]` and again on `[RECOVERED]`, so you're not just told once and left wondering.

### `log_watch.sh`
Tails the log files listed in `config.yaml`'s `log_paths` and greps new lines in real time for generic exploit/webshell indicators (`cmd=`, `eval(`, `base64_decode(`, `union select`, path traversal, reverse-shell patterns, etc.), alerting through the same webhook. Faster first signal than waiting on `watch_changes.py`'s next hash-diff cycle, and it catches request-based attacks that never touch a file. Patterns are generic since the exact stack isn't known yet — add stack-specific ones once you see what you're running.

### `patch_restore.sh`
Fast rollback of a tampered file/directory from the backup `blue_ops.sh` made. `./patch_restore.sh list` shows available backups; `./patch_restore.sh restore <backup_dir> <path>` finds the matching backed-up copy, quarantines the current (possibly tampered) version for later analysis, and restores the clean copy in place.

### `alert_notify.sh`
Shared alert helper sourced by `log_watch.sh` (and usable from any other bash script): `alert "message"` prints a timestamped line and, if `alert_webhook_url` is set in `config.yaml`, also POSTs it there.

### `setup_pwnbox.sh`
Workspace bootstrap for a fresh browser Pwnbox.
- Creates a standard folder layout under `~/ihack/` (`web`, `pwn`, `rev`, `crypto`, `forensics`, `scripts`).
- Downloads the Burp Suite Community Edition JAR into `~/ihack/scripts/`.
- Adds a `burp` alias to `~/.bashrc` that launches Burp via `java -jar`.

---

## Quick Start Inside Pwnbox / Target Box

### 1. Initialize Pwnbox Workspace (Run on your Pwnbox)
```bash
git clone <YOUR_REPO_URL> ~/ihack && cd ~/ihack
chmod +x *.sh *.py
./setup_pwnbox.sh
```