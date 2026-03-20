#!/bin/bash

# ---------------------------------------------------------------
# Fleet Demo Setup — Step 2: Start Machines
#
# All 20 machines need to connect at least once so they show
# a last-seen timestamp instead of "awaiting setup."
#
# This script:
#   1. Builds the viam-server Docker image (once)
#   2. Starts all 20 machines as Docker containers
#   3. Waits for them to connect and register with the cloud
#   4. Stops the 8 "offline" containers
#   5. Leaves the 12 "online" containers running
#
# Each container gets its own isolated filesystem, solving the
# shared ~/.viam package-cache conflict.
#
# Directory structure expected:
#   configs/all/<machine-name>.json   ← all 20 machine configs
#
# Usage:
#   ./start-online-machines.sh                    ← start all 20
#   ./start-online-machines.sh chi-pick-arm-01    ← start one machine
#   ./stop-online-machines.sh                     ← when done with the demo
# ---------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIGS_DIR="$SCRIPT_DIR/configs/all"
LOGS_DIR="$SCRIPT_DIR/logs"
IMAGE_NAME="viam-fleet-demo"
SINGLE_MACHINE="${1:-}"

# Machines that should go offline after initial connection
OFFLINE_MACHINES=(
  "aus-pick-arm-01"
  "aus-pick-arm-02"
  "chi-inspection-bot-02"
  "chi-conveyor-ctrl-02"
  "chi-pick-arm-02"
  "sea-inspection-bot-02"
  "sea-conveyor-ctrl-02"
  "sea-pick-arm-02"
)

# ---------------------------------------------------------------

if [[ ! -d "$CONFIGS_DIR" ]]; then
  echo "Error: $CONFIGS_DIR not found."
  echo "Create it and place all 20 machine config JSONs inside."
  exit 1
fi

if [[ -n "$SINGLE_MACHINE" ]]; then
  config_path="$CONFIGS_DIR/${SINGLE_MACHINE}.json"
  if [[ ! -f "$config_path" ]]; then
    echo "Error: no config found for '$SINGLE_MACHINE' at $config_path"
    exit 1
  fi
  configs=("$config_path")
else
  configs=("$CONFIGS_DIR"/*.json)
  if [[ ! -e "${configs[0]}" ]]; then
    echo "Error: no config files found in $CONFIGS_DIR"
    exit 1
  fi
fi

mkdir -p "$LOGS_DIR"

# ---------------------------------------------------------------
# Phase 1: Build the Docker image

echo ""
echo "Phase 1: Building Docker image ($IMAGE_NAME)..."
echo ""

docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile.viam-server" "$SCRIPT_DIR"

if [[ $? -ne 0 ]]; then
  echo "Error: Docker build failed."
  exit 1
fi

echo ""
echo "  Image built successfully."

# ---------------------------------------------------------------
# Phase 2: Start all 20 machines as containers

echo ""
echo "Phase 2: Starting all ${#configs[@]} machines..."
echo ""

for config in "${configs[@]}"; do
  machine_name=$(basename "$config" .json)
  container_name="viam-${machine_name}"
  log_file="$LOGS_DIR/${machine_name}.log"

  # Remove any existing stopped container with this name
  docker rm "$container_name" 2>/dev/null

  if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
    echo "  [already running] $machine_name"
    continue
  fi

  docker run -d \
    --name "$container_name" \
    -v "${config}:/etc/viam/config.json:ro" \
    "$IMAGE_NAME" \
    > /dev/null

  if [[ $? -eq 0 ]]; then
    echo "  [started] $machine_name → container: $container_name"
    # Stream logs to file in background
    docker logs -f "$container_name" > "$log_file" 2>&1 &
  else
    echo "  [failed]  $machine_name"
  fi
done

# ---------------------------------------------------------------
# Phase 3 & 4: Skip when starting a single machine

if [[ -n "$SINGLE_MACHINE" ]]; then
  echo ""
  echo "Single-machine mode — skipping wait and offline teardown."
  echo "Done. Container: viam-${SINGLE_MACHINE}"
  echo "Logs: docker logs -f viam-${SINGLE_MACHINE}"
  exit 0
fi

# ---------------------------------------------------------------
# Phase 3: Wait for all machines to connect

echo ""
echo "Phase 3: Waiting 60 seconds for all machines to register with the cloud..."
sleep 60

# ---------------------------------------------------------------
# Phase 4: Stop the offline machines

echo ""
echo "Phase 4: Stopping offline machines..."
echo ""

for machine_name in "${OFFLINE_MACHINES[@]}"; do
  container_name="viam-${machine_name}"

  if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
    docker stop "$container_name" > /dev/null
    echo "  [offline] $machine_name (container stopped)"
  else
    echo "  [already stopped] $machine_name"
  fi
done

# ---------------------------------------------------------------

online=$(docker ps --filter "name=viam-" --format '{{.Names}}' | wc -l | tr -d ' ')

echo ""
echo "Done."
echo "  Online  (still running): $online"
echo "  Offline (last-seen set): ${#OFFLINE_MACHINES[@]}"
echo ""
echo "Fleet is ready for the demo."
echo "Run ./stop-online-machines.sh when finished."
