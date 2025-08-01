#!/bin/bash

# usage: ./run.sh [conf.yaml]

CONFIG_FILE=${1:-conf.yaml}

# Move to the correct directory
cd "$(dirname "$0")/../root" || {
  echo "Failed to cd into clientportal.gw/root"
  exit 1
}

export RUNTIME_PATH=".:../dist/ibgroup.web.core.iblink.router.clientportal.gw.jar:../build/lib/runtime/*"

echo "running Java Gateway..."
echo " runtime path : $RUNTIME_PATH"
echo " config file  : $CONFIG_FILE"

java \
  -server \
  -Dvertx.disableDnsResolver=true \
  -Djava.net.preferIPv4Stack=true \
  -Dvertx.logger-delegate-factory-class-name=io.vertx.core.logging.SLF4JLogDelegateFactory \
  -Dnologback.statusListenerClass=ch.qos.logback.core.status.OnConsoleStatusListener \
  -Dnolog4j.debug=true \
  -Dnolog4j2.debug=true \
  -cp "$RUNTIME_PATH" \
  ibgroup.web.core.clientportal.gw.GatewayStart \
  --conf "$CONFIG_FILE"
