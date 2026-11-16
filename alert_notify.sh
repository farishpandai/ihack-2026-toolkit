#!/usr/bin/env bash
# Shared alert helper. Other scripts source this file and call `alert "message"`.
# If config.yaml has an alert_webhook_url set, the message is also POSTed there
# (Discord/Slack-compatible incoming webhook format) so alerts aren't missed
# when nobody is watching a terminal.
#
# Usage:
#   source ./alert_notify.sh
#   alert "[ALERT - MODIFIED] /var/www/html/index.php"

CONFIG_FILE="${CONFIG_FILE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/config.yaml}"

_webhook_url() {
    # Very small YAML read: pulls the value of alert_webhook_url: "..."
    grep -E '^alert_webhook_url:' "$CONFIG_FILE" 2>/dev/null \
        | sed -E 's/^alert_webhook_url:[[:space:]]*"?([^"]*)"?[[:space:]]*$/\1/'
}

alert() {
    local msg="$1"
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$ts] $msg"

    local url
    url="$(_webhook_url)"
    if [ -n "$url" ]; then
        # Discord accepts {"content": "..."}; Slack accepts the same key too.
        curl -s -X POST -H "Content-Type: application/json" \
            -d "{\"content\": \"[$ts] $msg\"}" \
            "$url" >/dev/null 2>&1 &
    fi
}
