#!/bin/bash
close_terminal_window() {
    if [ "${C4C_KEEP_TERMINAL:-}" != "1" ] && [ "${TERM_PROGRAM:-}" = "Apple_Terminal" ]; then
        osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1 &
    fi
}
trap close_terminal_window EXIT

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

pkill -f "${SCRIPT_DIR}/remote_keys.py"
pkill -f "remote_keys.py"
pkill -x "Control4Computer"
pkill -f "Control4Computer.app/Contents/MacOS/Control4Computer"
