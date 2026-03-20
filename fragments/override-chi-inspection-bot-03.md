# Error Config: chi-inspection-bot-03

This machine uses the standard `fragment-inspection-bot` fragment but has an additional
vision service added **directly on the machine** (not via the fragment) with a deliberate
attribute typo. This is the machine used for the diagnostics section of the demo.

## What it does

A `color-detector` vision service is added to the machine config with the attribute
`detect_colors` instead of the correct `detect_color`. This causes the detector to fail
on startup and emit continuous errors into the machine's log stream.

The machine itself stays online — making it a realistic "broken but not dead" scenario
that a field engineer would need to diagnose remotely.

## How to configure in app.viam.com

1. Open **chi-inspection-bot-03** → **Config** tab
2. Add a new vision service directly on this machine (not via fragment):
   - Name: `color-detector`
   - Model: `rdk:vision:color_detector`
3. Add the following attribute with the intentional typo:
   ```json
   {
     "detect_colors": ["#FF0000"]
   }
   ```
   (Correct attribute name is `detect_color` — the trailing `s` is the bug)
4. Save

## Demo flow

- Section 2: Fleet dashboard shows chi-inspection-bot-03 with an error indicator (online but unhealthy)
- Section 2: Click in → live log stream shows `color-detector` errors
- Section 2: Filter logs by ERROR level — detector failure isolated
- Section 2: Components tab — `color-detector` shows red / unhealthy
- Section 3: Edit the config in place, fix `detect_colors` → `detect_color`
- Section 3: Component goes green — machine recovers live

## Why this setup

- The machine stays **online** — more realistic than a full crash, and shows that Viam
  surfaces component-level health separately from machine connectivity
- A typo is immediately relatable — any engineer has done this
- The fix is a single character change — clean, fast demo moment
- Chicago having an issue while Austin is healthy makes the multi-location fleet view
  visually interesting
