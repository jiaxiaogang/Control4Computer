#!/bin/bash
close_terminal_window() {
    if [ "${TERM_PROGRAM:-}" = "Apple_Terminal" ]; then
        osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1 &
    fi
}
trap close_terminal_window EXIT

cd "$(dirname "$0")" || exit 1

C4C_KEEP_TERMINAL=1 ./MacStop.command
sleep 1
C4C_KEEP_TERMINAL=1 ./MacRun.command
