#!/usr/bin/env bash
# Tails the log files listed in config.yaml and greps, in real time, for
# generic indicators of webshell/exploit activity. This is a faster first
# signal than waiting for watch_changes.py's next hash-diff cycle, and it
# catches request-based attacks that don't modify any file at all.
#
# Patterns here are intentionally generic (not tied to one stack) since the
# service/framework isn't known yet. Add stack-specific patterns once you see
# what you're actually running.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/alert_notify.sh"

CONFIG_FILE="$SCRIPT_DIR/config.yaml"

# Pull log_paths out of config.yaml (simple line-based YAML read, no deps needed)
mapfile -t LOG_PATHS < <(
    awk '/^log_paths:/{flag=1; next} /^[a-zA-Z_]+:/{flag=0} flag && /^[[:space:]]*-/{
        gsub(/^[[:space:]]*-[[:space:]]*/, ""); print
    }' "$CONFIG_FILE"
)

EXISTING_PATHS=()
for p in "${LOG_PATHS[@]}"; do
    if [ -f "$p" ]; then
        EXISTING_PATHS+=("$p")
    fi
done

if [ "${#EXISTING_PATHS[@]}" -eq 0 ]; then
    echo "[!] None of the configured log_paths exist on this box yet."
    echo "    Edit config.yaml's log_paths once you know where your service logs."
    exit 1
fi

echo "[*] Watching: ${EXISTING_PATHS[*]}"

# Generic suspicious-request / webshell indicators. Case-insensitive.
PATTERN='(cmd=|eval\(|base64_decode\(|passthru\(|shell_exec\(|system\(|/\.\./|wget |curl .*http|nc -e|bash -i|powershell|union select|<\?php|\.\./\.\./)'

tail -F -n0 "${EXISTING_PATHS[@]}" 2>/dev/null | while read -r line; do
    if echo "$line" | grep -Eiq "$PATTERN"; then
        alert "[SUSPICIOUS LOG LINE] $line"
    fi
done
