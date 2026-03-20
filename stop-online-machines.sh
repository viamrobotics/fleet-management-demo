#!/bin/bash

# ---------------------------------------------------------------
# Fleet Demo Teardown: Stop and remove viam-* containers
#
# Usage:
#   ./stop-online-machines.sh                  ← stop all
#   ./stop-online-machines.sh chi-pick-arm-01  ← stop one
# ---------------------------------------------------------------

SINGLE_MACHINE="${1:-}"

if [[ -n "$SINGLE_MACHINE" ]]; then
  container="viam-${SINGLE_MACHINE}"
  if ! docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
    echo "No container found for '$SINGLE_MACHINE'."
    exit 1
  fi
  docker stop "$container" > /dev/null 2>&1
  docker rm   "$container" > /dev/null 2>&1
  echo "  [stopped] $SINGLE_MACHINE"
  exit 0
fi

echo ""
echo "Stopping all viam-* containers..."
echo ""

containers=$(docker ps -a --filter "name=viam-" --format '{{.Names}}')

if [[ -z "$containers" ]]; then
  echo "No viam-* containers found. Nothing to stop."
  exit 0
fi

stopped=0
while IFS= read -r container; do
  machine_name="${container#viam-}"
  docker stop "$container" > /dev/null 2>&1
  docker rm   "$container" > /dev/null 2>&1
  echo "  [stopped] $machine_name"
  ((stopped++))
done <<< "$containers"

echo ""
echo "Stopped and removed $stopped containers."
