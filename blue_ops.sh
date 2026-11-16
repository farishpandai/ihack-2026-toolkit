#!/usr/bin/env bash
# Run this immediately upon getting SSH/shell access to your team's A/D server

BACKUP_DIR="/root/.sys_bak_$(date +%H%M)"
PCAP_DIR="/root/.pcaps"

mkdir -p "$BACKUP_DIR" "$PCAP_DIR"
chmod 700 "$BACKUP_DIR" "$PCAP_DIR"

echo "[*] Backing up critical web, service, and config directories..."
for dir in /var/www /opt /srv /etc/nginx /etc/apache2 /etc/systemd/system; do
    if [ -d "$dir" ]; then
        cp -rp "$dir" "$BACKUP_DIR/" 2>/dev/null
    fi
done

echo "[*] Listing listening ports and active services..."
ss -tulpn > "$BACKUP_DIR/initial_ports.txt"
ps auxf > "$BACKUP_DIR/initial_processes.txt"

echo "[*] Starting rotating packet capture (50MB chunks, max 10 files)..."
# Captures incoming traffic on your own box (explicitly allowed by rules)
nohup tcpdump -i any -s 0 -C 50 -W 10 -w "$PCAP_DIR/capture.pcap" >/dev/null 2>&1 &

echo "[+] Backup complete at $BACKUP_DIR | tcpdump PID: $!"