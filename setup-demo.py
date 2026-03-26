#!/usr/bin/env python3
"""
setup-demo.py — One-command Fieldworks Robotics fleet demo setup

Sets up the complete 20-machine demo fleet in any Viam organization:
  1. Creates 3 locations (Austin Warehouse, Chicago Facility, Seattle Hub)
  2. Creates 3 fragments from local JSON files and uploads them
  3. Creates 20 machines across the 3 locations
  4. Applies the correct fragment to each machine
  4b. Adds color-detector misconfiguration to chi-inspection-bot-03
  5. Generates viam-server config files for all machines
  6. Starts the Docker fleet (12 online, 8 offline)

Usage:
    python3 setup-demo.py

Environment variables (prompted if not set):
    VIAM_API_KEY        — from app.viam.com → Org Settings → API Keys
    VIAM_API_KEY_ID     — the key's ID
    VIAM_ORG_ID         — your organization ID (from Org Settings)

Prerequisites:
    pip install viam-sdk
    Docker installed and running


"""

import asyncio
import getpass
import json
import os
import subprocess
import sys
from pathlib import Path

from viam.app.viam_client import ViamClient
from viam.rpc.dial import Credentials, DialOptions

# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent

MACHINES = [
    # Austin Warehouse — 5 online, 2 offline
    ("austin", "aus-inspection-bot-01", True),
    ("austin", "aus-inspection-bot-02", True),
    ("austin", "aus-inspection-bot-03", True),
    ("austin", "aus-conveyor-ctrl-01",  True),
    ("austin", "aus-conveyor-ctrl-02",  True),
    ("austin", "aus-pick-arm-01",       False),
    ("austin", "aus-pick-arm-02",       False),
    # Chicago Facility — 4 online, 3 offline
    ("chicago", "chi-inspection-bot-01", True),
    ("chicago", "chi-inspection-bot-03", True),
    ("chicago", "chi-conveyor-ctrl-01",  True),
    ("chicago", "chi-pick-arm-01",       True),
    ("chicago", "chi-inspection-bot-02", False),
    ("chicago", "chi-conveyor-ctrl-02",  False),
    ("chicago", "chi-pick-arm-02",       False),
    # Seattle Hub — 3 online, 3 offline
    ("seattle", "sea-inspection-bot-01", True),
    ("seattle", "sea-conveyor-ctrl-01",  True),
    ("seattle", "sea-pick-arm-01",       True),
    ("seattle", "sea-inspection-bot-02", False),
    ("seattle", "sea-conveyor-ctrl-02",  False),
    ("seattle", "sea-pick-arm-02",       False),
]

LOCATION_NAMES = {
    "austin":  "Austin",
    "chicago": "Chicago",
    "seattle": "Seattle",
}

FRAGMENT_FILES = {
    "inspection-bot": SCRIPT_DIR / "fragments" / "fragment-inspection-bot.json",
    "conveyor-ctrl":  SCRIPT_DIR / "fragments" / "fragment-conveyor-ctrl.json",
    "pick-arm":       SCRIPT_DIR / "fragments" / "fragment-pick-arm.json",
}

FRAGMENT_NAMES = {
    "inspection-bot": "fieldwork-inspection-bot",
    "conveyor-ctrl":  "fieldwork-conveyor-ctrl",
    "pick-arm":       "fieldwork-pick-arm",
}

OUTPUT_DIR = SCRIPT_DIR / "configs" / "all"
BASE_PORT  = 9090

# ---------------------------------------------------------------------------


def prompt(var: str, label: str, secret: bool = False) -> str:
    value = os.environ.get(var, "").strip()
    if value:
        return value
    return (getpass.getpass if secret else input)(f"{label}: ").strip()


def fragment_key_for(machine_name: str) -> str | None:
    for key in FRAGMENT_FILES:
        if key in machine_name:
            return key
    return None


# ---------------------------------------------------------------------------


async def main():
    print("\nFieldworks Robotics — Fleet Demo Setup")
    print("=" * 45)

    api_key    = prompt("VIAM_API_KEY",    "API Key",           secret=True)
    api_key_id = prompt("VIAM_API_KEY_ID", "API Key ID")
    org_id     = prompt("VIAM_ORG_ID",     "Organization ID")

    client = await ViamClient.create_from_dial_options(
        DialOptions(
            credentials=Credentials(type="api-key", payload=api_key),
            auth_entity=api_key_id,
        )
    )
    app = client.app_client

    # ------------------------------------------------------------------
    # Step 1: Locations
    # ------------------------------------------------------------------
    print("\nStep 1/6 — Locations")

    existing = {loc.name: loc for loc in await app.list_locations(org_id)}
    location_ids: dict[str, str] = {}

    for key, name in LOCATION_NAMES.items():
        if name in existing:
            location_ids[key] = existing[name].id
            print(f"  [exists]  {name}")
        else:
            loc = await app.create_location(org_id=org_id, name=name)
            location_ids[key] = loc.id
            print(f"  [created] {name}")

    # ------------------------------------------------------------------
    # Step 2: Fragments (create or update from local JSON files)
    # ------------------------------------------------------------------
    print("\nStep 2/6 — Fragments")

    existing_frags = {f.name: f for f in await app.list_fragments(org_id=org_id, show_public=False)}
    fragment_ids: dict[str, str] = {}

    for key, frag_name in FRAGMENT_NAMES.items():
        config = json.loads(FRAGMENT_FILES[key].read_text())
        if frag_name in existing_frags:
            frag = existing_frags[frag_name]
            await app.update_fragment(fragment_id=frag.id, name=frag_name, config=config)
            fragment_ids[key] = frag.id
            print(f"  [updated] {frag_name}")
        else:
            frag = await app.create_fragment(org_id=org_id, name=frag_name, config=config)
            fragment_ids[key] = frag.id
            print(f"  [created] {frag_name}")

    # ------------------------------------------------------------------
    # Step 3: Machines
    # ------------------------------------------------------------------
    print("\nStep 3/6 — Machines")

    existing_machines: dict[str, str] = {}  # name → id
    for key, loc_id in location_ids.items():
        for m in await app.list_robots(location_id=loc_id):
            existing_machines[m.name] = m.id

    machine_ids: dict[str, str] = {}

    for loc_key, machine_name, _ in MACHINES:
        if machine_name in existing_machines:
            machine_ids[machine_name] = existing_machines[machine_name]
            print(f"  [exists]  {machine_name}")
        else:
            robot_id = await app.new_robot(location_id=location_ids[loc_key], name=machine_name)
            machine_ids[machine_name] = robot_id
            print(f"  [created] {machine_name}")

    # ------------------------------------------------------------------
    # Step 4: Apply fragments
    # ------------------------------------------------------------------
    print("\nStep 4/6 — Applying fragments")

    for _, machine_name, _ in MACHINES:
        key = fragment_key_for(machine_name)
        if not key:
            continue

        frag_id   = fragment_ids[key]
        parts     = await app.get_robot_parts(robot_id=machine_ids[machine_name])
        main_part = next((p for p in parts if p.main_part), parts[0])
        config    = main_part.robot_config or {}
        frags     = config.get("fragments", [])

        if not any(f.get("id") == frag_id for f in frags):
            frags.append({"id": frag_id})

        await app.update_robot_part(
            robot_part_id=main_part.id,
            name=main_part.name,
            robot_config={**config, "fragments": frags},
        )
        print(f"  [applied] {machine_name} → {FRAGMENT_NAMES[key]}")

    # ------------------------------------------------------------------
    # Step 4b: Add color-detector misconfiguration to chi-inspection-bot-03
    #
    # Intentional typo: "detect_colors" (wrong) instead of "detect_color" (correct).
    # This is the erroring component shown in the Remote Diagnostics demo section.
    # ------------------------------------------------------------------
    print("\nStep 4b/6 — Adding color-detector misconfiguration to chi-inspection-bot-03")

    diag_machine = "chi-inspection-bot-03"
    parts     = await app.get_robot_parts(robot_id=machine_ids[diag_machine])
    main_part = next((p for p in parts if p.main_part), parts[0])
    config    = main_part.robot_config or {}
    services  = config.get("services", [])

    color_detector = {
        "name":  "color-detector",
        "api":   "rdk:service:vision",
        "model": "rdk:builtin:color_detector",
        "attributes": {
            "detect_colors": "#FF0000",   # typo: should be "detect_color"
            "hue_tolerance_pct": 0.73,
        },
    }

    # Replace if already present, otherwise append
    services = [s for s in services if s.get("name") != "color-detector"]
    services.append(color_detector)

    await app.update_robot_part(
        robot_part_id=main_part.id,
        name=main_part.name,
        robot_config={**config, "services": services},
    )
    print(f"  [applied] {diag_machine} — color-detector with 'detect_colors' typo")

    # ------------------------------------------------------------------
    # Step 5: Generate machine configs
    # ------------------------------------------------------------------
    print("\nStep 5/6 — Generating machine configs")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    port = BASE_PORT

    for _, machine_name, _ in MACHINES:
        parts     = await app.get_robot_parts(robot_id=machine_ids[machine_name])
        main_part = next((p for p in parts if p.main_part), parts[0])

        (OUTPUT_DIR / f"{machine_name}.json").write_text(json.dumps({
            "cloud": {
                "id":          main_part.id,
                "secret":      main_part.secret,
                "app_address": "https://app.viam.com:443",
            },
            "network": {
                "bind_address": f"localhost:{port}",
            },
        }, indent=2))

        print(f"  [wrote] {machine_name}.json  (port {port})")
        port += 1

    client.close()

    # ------------------------------------------------------------------
    # Step 6: Start Docker fleet
    # ------------------------------------------------------------------
    print("\nStep 6/6 — Starting Docker fleet")
    print()

    result = subprocess.run(
        ["bash", str(SCRIPT_DIR / "start-online-machines.sh")],
        cwd=SCRIPT_DIR,
    )

    print()
    print("=" * 45)
    print("Setup complete.")
    print()

    sys.exit(result.returncode)


if __name__ == "__main__":
    asyncio.run(main())
