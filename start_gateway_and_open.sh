#!/bin/bash

echo "Starting IBKR Gateway..."
sh ./venv/bin/run.sh root/conf.yaml &

sleep 5

echo "🌐 Attempting to open https://localhost:5000 in your default browser..."

case "$OSTYPE" in
  darwin*)  open https://localhost:5000 ;;  # macOS
  linux*)   xdg-open https://localhost:5000 ;;  # Linux
  cygwin*|msys*|win32*) start https://localhost:5000 ;;  # Windows
  *)        echo "❓ Unsupported OS: $OSTYPE. Please open https://localhost:5000 manually." ;;
esac
