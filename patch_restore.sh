#!/usr/bin/env bash
# Quick restore of a file or directory from the backup blue_ops.sh made at the
# start of the round. Pairs with watch_changes.py: when it alerts on a
# modified/new file, use this to roll it back fast instead of restoring by hand
# under pressure.
#
# Usage:
#   ./patch_restore.sh list                       # show available backups
#   ./patch_restore.sh restore <backup_dir> <path>  # restore one file/dir
#
# Example:
#   ./patch_restore.sh list
#   ./patch_restore.sh restore /root/.sys_bak_1430 /var/www/html/index.php

list_backups() {
    ls -1dt /root/.sys_bak_* 2>/dev/null || echo "[!] No backups found (did you run blue_ops.sh?)"
}

restore_path() {
    local backup_dir="$1"
    local target_path="$2"

    if [ ! -d "$backup_dir" ]; then
        echo "[!] Backup dir not found: $backup_dir"
        exit 1
    fi

    # blue_ops.sh backs up with `cp -rp /some/dir "$BACKUP_DIR/"`, so the
    # backed-up copy lives at $BACKUP_DIR/<basename of original parent dir>/...
    local rel="${target_path#/}"           # strip leading slash
    local candidate
    candidate="$(find "$backup_dir" -path "*${rel}" 2>/dev/null | head -n1)"

    if [ -z "$candidate" ]; then
        echo "[!] Couldn't find a backed-up copy of $target_path under $backup_dir"
        echo "    Browse $backup_dir manually to confirm the layout."
        exit 1
    fi

    echo "[*] Found backup copy: $candidate"
    echo "[*] Current target:    $target_path"

    local quarantine="/root/.quarantine_$(date +%H%M%S)"
    if [ -e "$target_path" ]; then
        mkdir -p "$quarantine"
        cp -rp "$target_path" "$quarantine/" 2>/dev/null
        echo "[*] Current (possibly tampered) version saved to $quarantine for later analysis"
    fi

    cp -rp "$candidate" "$target_path"
    echo "[+] Restored $target_path from backup."
}

case "$1" in
    list)
        list_backups
        ;;
    restore)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 restore <backup_dir> <path_to_restore>"
            exit 1
        fi
        restore_path "$2" "$3"
        ;;
    *)
        echo "Usage: $0 {list|restore <backup_dir> <path>}"
        exit 1
        ;;
esac
