#!/bin/bash
close_terminal_window() {
    if [ "${C4C_KEEP_TERMINAL:-}" != "1" ] && [ "${TERM_PROGRAM:-}" = "Apple_Terminal" ]; then
        osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1 &
    fi
}
trap close_terminal_window EXIT

cd "$(dirname "$0")" || exit 1

if [ -x ".venv/bin/pythonw" ]; then
    PYTHON=".venv/bin/pythonw"
elif [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    PYTHON="python"
fi

nohup "$PYTHON" "remote_keys.py" >/dev/null 2>&1 &
