#!/bin/bash
set -e

# ---------------------------------------------------------------
# Fleet Demo Setup — Step 1: Create Machines
# Creates 20 machines across 3 locations.
#
# Online/offline split (12 online, 8 offline):
#   Austin Warehouse  (7): 5 online, 2 offline
#   Chicago Facility  (7): 4 online, 3 offline
#   Seattle Hub       (6): 3 online, 3 offline
#
# After running this script:
#   1. Apply the correct fragment to each machine in app.viam.com
#      - aus-*/chi-*/sea-inspection-bot-* → fragment-inspection-bot
#      - aus-*/chi-*/sea-conveyor-ctrl-*  → fragment-conveyor-ctrl
#      - aus-*/chi-*/sea-pick-arm-*       → fragment-pick-arm
#   2. For each ONLINE machine, go to app.viam.com → machine → "Copy config"
#      and save the JSON into ./configs/online/<machine-name>.json
#   3. Run start-online-machines.sh
#
# Prerequisites:
#   1. `viam login` completed
#   2. Three locations created manually in app.viam.com
#   3. Fill in the location IDs below
# ---------------------------------------------------------------

LOCATION_AUSTIN="5wg0uxpczt"      # e.g. "abc123"
LOCATION_CHICAGO="bao861thux"     # e.g. "def456"
LOCATION_SEATTLE="ipbklc6oy5"     # e.g. "ghi789"

# ---------------------------------------------------------------

if [[ -z "$LOCATION_AUSTIN" || -z "$LOCATION_CHICAGO" || -z "$LOCATION_SEATTLE" ]]; then
  echo "Error: fill in all three location IDs at the top of this script before running."
  echo "Run 'viam locations list' to find them."
  exit 1
fi

# Format: "location_key|machine_name|status"
MACHINES=(
  # Austin Warehouse — 5 online, 2 offline
  "austin|aus-inspection-bot-01|online"
  "austin|aus-inspection-bot-02|online"
  "austin|aus-inspection-bot-03|online"
  "austin|aus-conveyor-ctrl-01|online"
  "austin|aus-conveyor-ctrl-02|online"
  "austin|aus-pick-arm-01|offline"
  "austin|aus-pick-arm-02|offline"

  # Chicago Facility — 4 online, 3 offline
  "chicago|chi-inspection-bot-01|online"
  "chicago|chi-inspection-bot-03|online"
  "chicago|chi-conveyor-ctrl-01|online"
  "chicago|chi-pick-arm-01|online"
  "chicago|chi-inspection-bot-02|offline"
  "chicago|chi-conveyor-ctrl-02|offline"
  "chicago|chi-pick-arm-02|offline"

  # Seattle Hub — 3 online, 3 offline
  "seattle|sea-inspection-bot-01|online"
  "seattle|sea-conveyor-ctrl-01|online"
  "seattle|sea-pick-arm-01|online"
  "seattle|sea-inspection-bot-02|offline"
  "seattle|sea-conveyor-ctrl-02|offline"
  "seattle|sea-pick-arm-02|offline"
)

get_location_id() {
  case "$1" in
    austin)  echo "$LOCATION_AUSTIN" ;;
    chicago) echo "$LOCATION_CHICAGO" ;;
    seattle) echo "$LOCATION_SEATTLE" ;;
  esac
}

mkdir -p configs/all

online_count=0
offline_count=0

echo ""
for entry in "${MACHINES[@]}"; do
  IFS="|" read -r loc_key machine_name status <<< "$entry"
  location_id=$(get_location_id "$loc_key")

  if [[ "$status" == "online" ]]; then
    echo "  [online]  $machine_name"
    ((online_count++))
  else
    echo "  [offline] $machine_name"
    ((offline_count++))
  fi

  viam machines create --name="$machine_name" --location="$location_id"
done

echo ""
echo "Done. Created $((online_count + offline_count)) machines."
echo "  Online  (need viam-server config): $online_count"
echo "  Offline (no action needed):        $offline_count"
echo ""
echo "Next steps:"
echo "  1. Create fragments in app.viam.com and run: python3 apply-fragments.py"
echo "  2. Add the color-detector misconfiguration to chi-inspection-bot-03 (see README)"
echo "  3. Run: python3 generate-configs.py"
echo "  4. Run: ./start-online-machines.sh"
