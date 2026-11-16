#!/usr/bin/env bash
# Periodic check for common attacker persistence mechanisms that watch_changes.py
# can't see (it only hashes files under /var/www, /opt, /srv). Run this once
# right after blue_ops.sh to set a baseline, then again anytime you suspect
# you've been popped, or on a timer (e.g. via a loop or cron on your OWN box —
# this does not touch firewall config, so it's within the rules).
#
# Usage:
#   ./persistence_check.sh baseline   # save current state as the baseline
#   ./persistence_check.sh check      # diff current state against baseline

BASELINE_DIR="/root/.persistence_baseline"
mkdir -p "$BASELINE_DIR"

snapshot() {
    local out_dir="$1"
    mkdir -p "$out_dir"

    # Cron jobs (system-wide + all users)
    { crontab -l 2>/dev/null; cat /etc/crontab 2>/dev/null; cat /etc/cron.d/* 2>/dev/null; } \
        > "$out_dir/cron.txt"

    # SSH authorized_keys for every user with a home dir
    find /root /home -maxdepth 3 -name "authorized_keys" -exec sh -c \
        'echo "== {} =="; cat "{}"' \; > "$out_dir/authorized_keys.txt" 2>/dev/null

    # SUID/SGID binaries system-wide
    find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null \
        | sort > "$out_dir/suid_sgid.txt"

    # Enabled systemd services/units
    systemctl list-unit-files --type=service 2>/dev/null \
        | sort > "$out_dir/systemd_units.txt"

    # Users with a login shell (new accounts show up here)
    awk -F: '$7 !~ /nologin|false/ {print $1":"$3":"$7}' /etc/passwd \
        | sort > "$out_dir/shell_users.txt"
}

case "$1" in
    baseline)
        snapshot "$BASELINE_DIR"
        echo "[+] Baseline saved to $BASELINE_DIR"
        ;;
    check)
        if [ ! -d "$BASELINE_DIR" ] || [ -z "$(ls -A "$BASELINE_DIR" 2>/dev/null)" ]; then
            echo "[!] No baseline found. Run './persistence_check.sh baseline' first."
            exit 1
        fi
        TMP_DIR="$(mktemp -d)"
        snapshot "$TMP_DIR"

        FOUND=0
        for f in cron.txt authorized_keys.txt suid_sgid.txt systemd_units.txt shell_users.txt; do
            if ! diff -q "$BASELINE_DIR/$f" "$TMP_DIR/$f" >/dev/null 2>&1; then
                echo "[ALERT - CHANGED] $f"
                diff "$BASELINE_DIR/$f" "$TMP_DIR/$f"
                FOUND=1
            fi
        done

        rm -rf "$TMP_DIR"
        if [ "$FOUND" -eq 0 ]; then
            echo "[*] No persistence changes detected."
        fi
        ;;
    *)
        echo "Usage: $0 {baseline|check}"
        exit 1
        ;;
esac
