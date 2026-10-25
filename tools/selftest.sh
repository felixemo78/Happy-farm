#!/bin/bash
# dev-only: run index.html?selftest in headless Chrome, print page console lines, exit 0 only on SELFTEST PASS
D="$(cd "$(dirname "$0")/.." && pwd -W 2>/dev/null || pwd)"
OUT=$(timeout 60 "/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --autoplay-policy=no-user-gesture-required --user-data-dir="$TEMP/hfchrome" --enable-logging=stderr --v=0 --virtual-time-budget=6000 --dump-dom "file:///$D/index.html?selftest" 2>&1 >/dev/null | grep CONSOLE)
echo "$OUT"
echo "$OUT" | grep -q "SELFTEST PASS"
