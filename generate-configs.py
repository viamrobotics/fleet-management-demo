#!/usr/bin/env python3
"""
Fleet Demo Setup — Step 1.5: Generate Machine Configs

Fetches credentials for all machines across the 3 demo locations
and writes viam-server config JSONs into configs/all/.

Prerequisites:
    pip install viam-sdk
    Create an API key at app.viam.com → Organization Settings → API Keys

Usage:
    python3 generate-configs.py
"""

import asyncio
import json
import os
from viam.app.viam_client import ViamClient
from viam.rpc.dial import DialOptions, Credentials

# ---------------------------------------------------------------
# Fill these in before running

API_KEY    = ""   # from app.viam.com → Org Settings → API Keys
API_KEY_ID = ""   # the key's ID (shown alongside the key)

LOCATION_IDS = [
    "",   # Austin   — run `viam locations list` to find
    "",   # Chicago
    "",   # Seattle
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "configs", "all")

# Each viam-server instance needs a unique port since they all run
# on the same machine. Ports are assigned starting from BASE_PORT.
BASE_PORT = 9090

# ---------------------------------------------------------------

async def main():
    if not API_KEY or not API_KEY_ID:
        print("Error: fill in API_KEY and API_KEY_ID before running.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dial_options = DialOptions(
        credentials=Credentials(type="api-key", payload=API_KEY),
        auth_entity=API_KEY_ID,
    )

    client = await ViamClient.create_from_dial_options(dial_options)
    app = client.app_client

    total = 0
    port = BASE_PORT

    for location_id in LOCATION_IDS:
        machines = await app.list_robots(location_id=location_id)

        for machine in machines:
            parts = await app.get_robot_parts(robot_id=machine.id)

            # Use the main part (first part) for the viam-server config
            main_part = next((p for p in parts if p.main_part), parts[0])

            config = {
                "cloud": {
                    "id": main_part.id,
                    "secret": main_part.secret,
                    "app_address": "https://app.viam.com:443",
                },
                "network": {
                    "bind_address": f"localhost:{port}",
                },
            }

            filename = os.path.join(OUTPUT_DIR, f"{machine.name}.json")
            with open(filename, "w") as f:
                json.dump(config, f, indent=2)

            print(f"  [wrote] {machine.name}.json  (port {port})")
            total += 1
            port += 1

    client.close()
    print(f"\nDone. Wrote {total} configs to {OUTPUT_DIR}/")
    print("Run ./start-online-machines.sh to start the fleet.")


if __name__ == "__main__":
    asyncio.run(main())
