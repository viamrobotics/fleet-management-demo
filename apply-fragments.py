#!/usr/bin/env python3
"""
Fleet Demo Setup — Step 1.75: Apply Fragments to Machines

Applies the correct fragment to each machine based on its name.
Run this after create-fleet-demo.sh and after creating the three
fragments in app.viam.com.

Prerequisites:
    pip install viam-sdk
    Three fragments created in app.viam.com — copy their IDs below.

Usage:
    python3 apply-fragments.py
"""

import asyncio
from viam.app.viam_client import ViamClient
from viam.rpc.dial import DialOptions, Credentials

# ---------------------------------------------------------------

API_KEY    = ""   # from app.viam.com → Org Settings → API Keys
API_KEY_ID = ""   # the key's ID (shown alongside the key)

LOCATION_IDS = [
    "",   # Austin   — run `viam locations list` to find
    "",   # Chicago
    "",   # Seattle
]

# Fragment IDs — copy from app.viam.com → Fleet → Fragments after creating each fragment
FRAGMENT_IDS = {
    "inspection-bot": "",   # fieldwork-inspection-bot
    "conveyor-ctrl":  "",   # fieldwork-conveyor-ctrl
    "pick-arm":       "",   # fieldwork-pick-arm
}

# ---------------------------------------------------------------

def get_fragment_key(machine_name: str) -> str | None:
    for key in FRAGMENT_IDS:
        if key in machine_name:
            return key
    return None


async def main():
    if not all(FRAGMENT_IDS.values()):
        print("Error: fill in all three fragment IDs before running.")
        print("Find them in app.viam.com → Fleet → Fragments.")
        return

    dial_options = DialOptions(
        credentials=Credentials(type="api-key", payload=API_KEY),
        auth_entity=API_KEY_ID,
    )

    client = await ViamClient.create_from_dial_options(dial_options)
    app = client.app_client

    applied = 0
    skipped = 0

    for location_id in LOCATION_IDS:
        machines = await app.list_robots(location_id=location_id)

        for machine in machines:
            fragment_key = get_fragment_key(machine.name)

            if not fragment_key:
                print(f"  [skipped] {machine.name} — no matching fragment")
                skipped += 1
                continue

            fragment_id = FRAGMENT_IDS[fragment_key]
            parts = await app.get_robot_parts(robot_id=machine.id)
            main_part = next((p for p in parts if p.main_part), parts[0])

            # Get the current config, add the fragment to it, and write it back
            current_config = main_part.robot_config or {}
            existing_fragments = current_config.get("fragments", [])

            # Avoid duplicate fragment entries
            if not any(f.get("id") == fragment_id for f in existing_fragments):
                existing_fragments.append({"id": fragment_id})

            updated_config = {**current_config, "fragments": existing_fragments}

            await app.update_robot_part(
                robot_part_id=main_part.id,
                name=main_part.name,
                robot_config=updated_config,
            )

            print(f"  [applied] {machine.name} → fieldwork-{fragment_key}")
            applied += 1

    client.close()
    print(f"\nDone. Applied: {applied}  Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
