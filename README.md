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
| Austin | 7 | 5 | 2 |
| Chicago | 7 | 4 | 3 |
| Seattle | 6 | 3 | 3 |

### Machine Types

Each location runs three types of machines, all using simulated hardware (`fieldwork:fake-modules-go`) — no physical robots required.

| Type | Naming | Fragment | Components |
|---|---|---|---|
| Inspection bot | `*-inspection-bot-*` | `fieldwork-inspection-bot` | board, front-cam, lidar, IMU, drive-base, vision detector |
| Conveyor controller | `*-conveyor-ctrl-*` | `fieldwork-conveyor-ctrl` | board, belt-motor, entry-sensor, exit-sensor, event-manager |
| Pick-and-place arm | `*-pick-arm-*` | `fieldwork-pick-arm` | board, arm, gripper, wrist-cam, force-sensor, vision detector |

### Full Machine List

**Austin** (5 online, 2 offline)
- `aus-inspection-bot-01` — online
- `aus-inspection-bot-02` — online
- `aus-inspection-bot-03` — online
- `aus-conveyor-ctrl-01` — online
- `aus-conveyor-ctrl-02` — online
- `aus-pick-arm-01` — offline
- `aus-pick-arm-02` — offline

**Chicago** (4 online, 3 offline)
- `chi-inspection-bot-01` — online
- `chi-conveyor-ctrl-01` — online
- `chi-pick-arm-01` — online
- `chi-inspection-bot-03` — online ⚠️ (error machine — component unhealthy, see below)
- `chi-inspection-bot-02` — offline
- `chi-conveyor-ctrl-02` — offline
- `chi-pick-arm-02` — offline

**Seattle** (3 online, 3 offline)
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

- Python 3.9+ with `viam-sdk` (`pip install viam-sdk`)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- A Viam API key — create one at **app.viam.com → Org Settings → API Keys**

---

## Setup

One command sets up everything — locations, fragments, machines, configs, and Docker fleet — whether the org is brand new or already partially configured:

```bash
python3 setup-demo.py
```

You'll be prompted for three values (or set them as environment variables):

| Variable | Where to find it |
|---|---|
| `VIAM_API_KEY` | app.viam.com → Org Settings → API Keys |
| `VIAM_API_KEY_ID` | shown alongside the key |
| `VIAM_ORG_ID` | app.viam.com → Org Settings |

The script runs six steps and is fully idempotent — safe to re-run if anything fails:

1. Creates the Austin, Chicago, and Seattle locations (skips any that already exist)
2. Creates the three fragments from local JSON files, or updates them if they exist
3. Creates all 20 machines (skips any that already exist)
4. Applies the correct fragment to each machine
5. Generates `configs/all/<machine>.json` for all 20 machines
6. Builds the Docker image and starts the fleet (12 online, 8 offline)

Setup takes about 3–5 minutes on first run (Docker build downloads viam-server). Re-runs are faster.

---

## Pre-Demo Checklist

Run through this before every demo to confirm everything is in the right state.

- [ ] app.viam.com shows **12 online** machines and **8 offline** across the fleet
- [ ] `chi-inspection-bot-03` shows as **online with an error indicator** (not offline)
- [ ] `chi-inspection-bot-03` → Components tab — `color-detector` shows red/unhealthy
- [ ] Austin inspection bots (`aus-inspection-bot-01/02/03`) are **not** pinned to a fragment version — they should be on `latest` before the canary section
- [ ] Note the current version number of `fieldwork-inspection-bot` (shown on the fragment detail page) — you'll pin Austin to this version during Section 4

If machines aren't running, start the fleet:

```bash
./start-online-machines.sh
```

---

## Running the Demo

### Start all machines

```bash
./start-online-machines.sh
```

1. Builds the Docker image (first run takes ~3 min to download viam-server)
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

---

## Demo Script

### Section 1 — The Fleet at a Glance

> "Fieldworks runs 20 robots across three warehouse facilities. Every one of them is managed from this single dashboard."

1. Open app.viam.com → Fieldworks Robotics
2. Show the **Locations** view — Austin, Chicago, Seattle each with machine counts and online/offline status
3. Click into **Austin** — 5 green machines, 2 grey (offline pick arms)
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
1. Navigate to **Austin** → open `aus-inspection-bot-01` → **Config** tab
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

1. In **Fleet → Fragments → fieldwork-inspection-bot**, make a visible change to the fragment — for example, update an attribute on the `detector` service
2. Save — this creates a new fragment version
3. Navigate to **Chicago** → `chi-inspection-bot-01` — it's on `latest`, so it's already running the new fragment version (check the fragment version shown on its Config tab)
4. Navigate to **Austin** → `aus-inspection-bot-01` — still on the pinned version, unchanged
5. Point to the fragment version indicator on each machine to make the split visible

**What to point out:** The update reached Chicago and Seattle the moment you saved — no deployment pipeline, no SSH, no maintenance window. Austin is completely unaffected. When you're confident the new config is solid, remove the version pin on the Austin machines and the rollout completes. This scales identically to 2,000 machines.

---

## File Reference

```
fleet-management-demo/
├── README.md                        ← this file
├── .gitignore
├── setup-demo.py                    ← one-command setup (run this)
├── start-online-machines.sh         ← start 12 online / stop 8 offline via Docker
├── stop-online-machines.sh          ← stop and remove viam-* containers
├── Dockerfile.viam-server           ← Ubuntu 22.04 image with viam-server AppImage
├── fragments/
│   ├── fragment-inspection-bot.json ← shared config for all inspection bots
│   ├── fragment-conveyor-ctrl.json  ← shared config for all conveyor controllers
│   └── fragment-pick-arm.json       ← shared config for all pick-and-place arms
└── configs/all/                     ← gitignored — machine credentials, generated by setup-demo.py
```

The following scripts are kept for reference if you need to run individual steps manually. `setup-demo.py` reimplements all of this end-to-end:

- `create-fleet-demo.sh` — creates machines via CLI (fill in location IDs at the top)
- `apply-fragments.py` — applies fragments to machines (fill in location and fragment IDs at the top)
- `generate-configs.py` — fetches machine credentials and writes config JSONs (fill in location IDs at the top)

---

## How It Works (Technical)

Each machine runs as a Docker container with its own isolated filesystem and its own `/root/.viam` package cache — no shared state between instances. The containers download the real viam-server AppImage at build time and connect to app.viam.com using genuine machine credentials, so they appear as live machines in the dashboard.

All hardware is simulated via `fieldwork:fake-modules-go`, which implements the full Viam component API for cameras, arms, motors, sensors, and more. A fake vision service (`rdk:builtin:fake`) stands in for the object detector — it's present to show the capability and integration in the component graph.

---

## Troubleshooting

**Machines show "awaiting setup" after start**
The container hasn't connected yet. Wait 30–60 seconds and refresh. If it persists:
```bash
docker logs viam-<machine-name>
```

**Multiple orgs causing container conflicts**
If you've run the demo against more than one org, Docker container names will collide. Nuke all viam containers and re-run setup:
```bash
docker ps -a --filter "name=viam-" -q | xargs docker rm -f
python3 setup-demo.py
```

**Docker build fails**
Make sure Docker Desktop is running. The build downloads a ~30 MB AppImage and needs a network connection.

**Watch a machine's logs live**
```bash
docker logs -f viam-chi-inspection-bot-03
```
