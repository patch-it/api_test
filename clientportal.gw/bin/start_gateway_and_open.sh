#!/bin/bash

echo "Starting IBKR Gateway..."
bash clientportal.gw/bin/run.sh conf.yaml &
sleep 5

echo "🌐 Attempting to open https://localhost:5000 in your default browser..."

case "$OSTYPE" in
  darwin*)  open https://localhost:5000 ;;
  linux*)   xdg-open https://localhost:5000 ;;
  cygwin*|msys*|win32*) start https://localhost:5000 ;;
  *)        echo "❓ Unsupported OS: $OSTYPE. Please open https://localhost:5000 manually." ;;
esac
