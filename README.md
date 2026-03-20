# Fieldworks Robotics — Fleet Management Demo

A simulated 20-machine industrial robotics fleet across 3 warehouse locations, built on Viam. Demonstrates fleet visibility, remote diagnostics, config-as-code, canary deployments, and OTA updates — all from a single dashboard with no on-site access.

---

## What This Demo Shows

A fictional industrial robotics company — **Fieldworks Robotics** — runs pick-and-place lines across three facilities. The demo is five sections:

1. **Fleet at a Glance** — 20 machines across 3 locations, 12 online / 8 offline, all visible in one dashboard without any on-prem infrastructure
2. **Remote Diagnostics** — `chi-inspection-bot-03` is online but unhealthy; drill into its logs and component status to identify a misconfigured detector without physical access
3. **Live Config Fix** — correct the misconfiguration from the dashboard and watch the component recover in real time
4. **Canary Testing** — pin the Austin inspection bots to a stable fragment version, leaving Chicago and Seattle as canary testers
5. **OTA Update** — push a config change to the fragment and show it propagating to canary machines only, leaving Austin untouched

---

## Organization Structure

**Org:** Fieldworks Robotics

| Location | Machines | Online | Offline |
|---|---|---|---|
| Austin Warehouse | 7 | 5 | 2 |
| Chicago Facility | 7 | 4 | 3 |
| Seattle Hub | 6 | 3 | 3 |

### Machine Types

Each location runs three types of machines, all using simulated hardware (`rand:fake-modules-go`) — no physical robots required.

| Type | Naming | Fragment | Components |
|---|---|---|---|
| Inspection bot | `*-inspection-bot-*` | `fieldwork-inspection-bot` | board, front-cam, lidar, IMU, drive-base, YOLOv8 detector |
| Conveyor controller | `*-conveyor-ctrl-*` | `fieldwork-conveyor-ctrl` | board, belt-motor, entry-sensor, exit-sensor, event-manager |
| Pick-and-place arm | `*-pick-arm-*` | `fieldwork-pick-arm` | board, arm, gripper, wrist-cam, force-sensor, YOLOv8 detector |

### Full Machine List

**Austin Warehouse** (5 online, 2 offline)
- `aus-inspection-bot-01` — online
- `aus-inspection-bot-02` — online
- `aus-inspection-bot-03` — online
- `aus-conveyor-ctrl-01` — online
- `aus-conveyor-ctrl-02` — online
- `aus-pick-arm-01` — offline
- `aus-pick-arm-02` — offline

**Chicago Facility** (4 online, 3 offline)
- `chi-inspection-bot-01` — online
- `chi-conveyor-ctrl-01` — online
- `chi-pick-arm-01` — online
- `chi-inspection-bot-03` — online ⚠️ (error machine — component unhealthy, see below)
- `chi-inspection-bot-02` — offline
- `chi-conveyor-ctrl-02` — offline
- `chi-pick-arm-02` — offline

**Seattle Hub** (3 online, 3 offline)
- `sea-inspection-bot-01` — online
- `sea-conveyor-ctrl-01` — online
- `sea-pick-arm-01` — online
- `sea-inspection-bot-02` — offline
- `sea-conveyor-ctrl-02` — offline
- `sea-pick-arm-02` — offline

### The Error Machine

`chi-inspection-bot-03` is online but has a deliberate misconfiguration: a `color-detector` vision service has been added directly to its config with the attribute named `detect_colors` instead of the correct `detect_color`. This causes the detector to fail on startup and emit errors into the log stream while the machine itself stays connected — a realistic "something's wrong but the robot is still running" scenario.

---

## Prerequisites

- [Viam CLI](https://docs.viam.com/cli/) installed and logged in (`viam login`)
- Python 3.9+ with `viam-sdk` (`pip install viam-sdk`)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- Access to the **Fieldworks Robotics** org on app.viam.com
- A Viam API key for the org — create one at **app.viam.com → Org Settings → API Keys**

---

## Setup (One-Time)

This only needs to be done once. If the org is already configured in app.viam.com, skip to **Pre-Demo Checklist**.

### Step 0 — Fill in your API credentials

Open `apply-fragments.py` and `generate-configs.py` and fill in the same values at the top of each:

```python
API_KEY    = ""   # from app.viam.com → Org Settings → API Keys
API_KEY_ID = ""   # the key's ID (shown alongside the key)
```

### Step 1 — Create the machines

```bash
./create-fleet-demo.sh
```

Creates all 20 machines across the 3 locations using the Viam CLI.

### Step 2 — Create the fragments in app.viam.com

Navigate to **app.viam.com → Fieldworks Robotics → Fleet → Fragments** and create three fragments using the JSON files in `fragments/`:

| Fragment name | File |
|---|---|
| `fieldwork-inspection-bot` | `fragments/fragment-inspection-bot.json` |
| `fieldwork-conveyor-ctrl` | `fragments/fragment-conveyor-ctrl.json` |
| `fieldwork-pick-arm` | `fragments/fragment-pick-arm.json` |

After saving each fragment, copy its ID from the fragment detail page. Open `apply-fragments.py` and paste the IDs into the `FRAGMENT_IDS` dict at the top of the file.

### Step 3 — Apply fragments to all machines

```bash
python3 apply-fragments.py
```

Assigns the correct fragment to each machine based on its name. Takes about 30 seconds.

### Step 4 — Add the broken color detector to `chi-inspection-bot-03`

1. Open **chi-inspection-bot-03** in app.viam.com → **Config** tab
2. Add a new **vision service** directly on this machine (not via the fragment):
   - Name: `color-detector`
   - Model: `rdk:vision:color_detector`
   - Attributes:
     ```json
     { "detect_colors": ["#FF0000"] }
     ```
     > The attribute name `detect_colors` is intentionally wrong — the correct name is `detect_color`. This typo causes the service to fail on startup.
3. Save


---

## Pre-Demo Checklist

Run through this before every demo to confirm everything is in the right state.

- [ ] `configs/all/` exists — if not, run `python3 generate-configs.py` first (one-time per machine)
- [ ] `./start-online-machines.sh` has been run — all 20 containers started
- [ ] app.viam.com shows **12 online** machines and **8 offline** across the fleet
- [ ] `chi-inspection-bot-03` shows as **online with an error indicator** (not offline)
- [ ] `chi-inspection-bot-03` → Components tab — `color-detector` shows red/unhealthy
- [ ] Austin inspection bots (`aus-inspection-bot-01/02/03`) are **not** pinned to a fragment version — they should be on `latest` before the canary section
- [ ] Note the current version number of `fieldwork-inspection-bot` (shown on the fragment detail page) — you'll pin Austin to this version during Section 4

---

## Running the Demo

### Start all machines

```bash
./start-online-machines.sh
```

1. Builds the Docker image (first run takes ~2 min to download viam-server)
2. Starts all 20 machines as Docker containers
3. Waits 60 seconds for them to register with app.viam.com
4. Stops the 8 machines that should appear offline

### Start a single machine (for troubleshooting)

```bash
./start-online-machines.sh chi-pick-arm-01
```

Starts just that one container. No wait, no offline teardown.

### Stop everything

```bash
./stop-online-machines.sh                   # stop all
./stop-online-machines.sh chi-pick-arm-01   # stop one machine
```

Stops and removes the specified container(s).

---

## Demo Script

### Section 1 — The Fleet at a Glance

> "Fieldworks runs 20 robots across three warehouse facilities. Every one of them is managed from this single dashboard."

1. Open app.viam.com → Fieldworks Robotics
2. Show the **Locations** view — Austin, Chicago, Seattle each with machine counts and online/offline status
3. Click into **Austin Warehouse** — 5 green machines, 2 grey (offline pick arms)
4. Switch to the **Fleet** tab — all 20 machines in one list; show the location filter

**What to point out:** Three cities, zero on-prem infrastructure. No VPN, no static IPs, no on-site server. Any machine that has an internet connection is visible and manageable here.

---

### Section 2 — Diagnose Without Being There

> "Chicago has a problem. Let's see what's wrong without getting on a plane."

1. From the fleet list, point out **chi-inspection-bot-03** — it has an error indicator but it's still online
2. Click into it → **Logs** tab
3. Show the live log stream — `color-detector` errors scrolling in
4. Use the log level filter to isolate **ERROR** — the failing service is immediately obvious
5. Click the **Components** tab — `color-detector` shows red/unhealthy while everything else is green

**What to point out:** The machine is still running — this isn't a crash, it's a misconfiguration. Without Viam, someone would need to notice the issue through downstream quality failures, then physically visit to connect a laptop and read logs. Here you caught it remotely in seconds.

---

### Section 3 — Fix It From the Dashboard

> "There's a typo in the config. One character. We can fix it right here."

1. On **chi-inspection-bot-03** → **Config** tab, find the `color-detector` service
2. Show the attribute `detect_colors` — point out the typo (correct name is `detect_color`)
3. Fix the attribute name in place and save
4. Switch to the **Components** tab — watch `color-detector` go green within seconds as viam-server reconfigures live

**What to point out:** No SSH. No redeployment. No maintenance window. The config change pushed over the existing cloud connection and the robot reconfigured itself. This is what "software-defined hardware" means in practice.

---

### Section 4 — Canary Testing

> "We don't push changes to 20 machines at once. Here's how we control rollout."

> ⚠️ Do steps 1–3 before starting this section in front of a customer — pinning machines one-by-one is setup, not demo.

**Pre-section setup** (takes ~2 min, do while talking through the concept):
1. Navigate to **Austin Warehouse** → open `aus-inspection-bot-01` → **Config** tab
2. Find the `fieldwork-inspection-bot` fragment entry and pin it to the current version number (visible on the fragment detail page, e.g. `3`)
3. Repeat for `aus-inspection-bot-02` and `aus-inspection-bot-03`

**Demo narrative:**
1. Open **Fleet → Fragments → fieldwork-inspection-bot**
2. Show that Chicago and Seattle inspection bots are on `latest` — they get every change the moment you save
3. Show that Austin inspection bots are pinned to version `3` — they're locked to the last known-good config
4. Explain the split: **Austin = stable, Chicago + Seattle = canary testers**

**What to point out:** No separate staging environment. No feature flags infrastructure. The entire rollout strategy is a version number in a config field. You can see exactly what version every machine is running from the fleet view — and change it from the same place.

---

### Section 5 — OTA Update to Canary Machines

> "New config ships to the canary machines first. Austin doesn't move until we're confident."

1. In **Fleet → Fragments → fieldwork-inspection-bot**, make a visible change — increase the `confidence_threshold` on the YOLOv8 detector from `0.6` to `0.75`
2. Save — this creates a new fragment version
3. Navigate to **Chicago Facility** → `chi-inspection-bot-01` — it's on `latest`, so it's already running the new fragment version (check the fragment version shown on its Config tab)
4. Navigate to **Austin Warehouse** → `aus-inspection-bot-01` — still on version `3`, unchanged
5. Point to the fragment version indicator on each machine to make the split visible

**What to point out:** The update reached Chicago and Seattle the moment you saved — no deployment pipeline, no SSH, no maintenance window. Austin is completely unaffected. When you're confident the new config is solid, remove the version pin on the Austin machines and the rollout completes. This scales identically to 2,000 machines.

---

## File Reference

```
marketing/
├── README.md                        ← this file
├── .gitignore
├── create-fleet-demo.sh             ← Step 1: create 20 machines via CLI
├── apply-fragments.py               ← Step 3: apply fragments to all machines
├── generate-configs.py              ← fetch credentials and write config JSONs (run once per machine)
├── start-online-machines.sh         ← start 12 online / stop 8 offline via Docker
├── stop-online-machines.sh          ← stop and remove viam-* containers
├── Dockerfile.viam-server           ← Ubuntu 22.04 image with viam-server AppImage
├── fragments/
│   ├── fragment-inspection-bot.json ← shared config for all inspection bots
│   ├── fragment-conveyor-ctrl.json  ← shared config for all conveyor controllers
│   ├── fragment-pick-arm.json       ← shared config for all pick-and-place arms
│   └── override-chi-inspection-bot-03.md  ← documents the error machine setup
└── configs/all/                     ← gitignored — machine credentials, generated locally
```

---

## How It Works (Technical)

Each machine runs as a Docker container with its own isolated filesystem and its own `/root/.viam` package cache — no shared state between instances. The containers download the real viam-server AppImage at build time and connect to app.viam.com using genuine machine credentials, so they appear as live machines in the dashboard.

All hardware is simulated via `rand:fake-modules-go`, which implements the full Viam component API for cameras, arms, motors, sensors, and more. The YOLOv8 detector runs but returns no detections (fake cameras return empty frames) — it's present to show the capability and integration, not to produce results.

---

## Troubleshooting

**Machines show "awaiting setup" after start**
The container hasn't connected yet. Wait 30–60 seconds and refresh. If it persists:
```bash
docker logs viam-<machine-name>
```

**Docker build fails**
Make sure Docker Desktop is running. The build downloads a ~30 MB AppImage and needs a network connection.

**A module fails to start**
```bash
docker logs viam-<machine-name>
```
Common fix: stop everything and rebuild the image, which picks up any missing system libraries.
```bash
./stop-online-machines.sh && ./start-online-machines.sh
```

**`generate-configs.py` returns no machines**
The location IDs at the top of the script need to match app.viam.com. Run `viam locations list` to verify.

**Watch a machine's logs live**
```bash
docker logs -f viam-chi-inspection-bot-03
```
