#!/usr/bin/env bash
# Close the Coworker Tray (and its window) if it is running. Run from code/.
set -euo pipefail

if command -v powershell >/dev/null 2>&1; then
  # Only python processes: this PowerShell's own command line names the module too.
  count=$(powershell -NoProfile -Command '$p = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -like "python*" -and $_.CommandLine -like "*-m desktop.tray*" }); $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; $p.Count' | tr -d '\r')
else
  count=$(pkill -f -- "-m desktop.tray" && echo 1 || echo 0)
fi
if [ "${count:-0}" != "0" ]; then echo "tray stopped."; else echo "tray was not running."; fi
