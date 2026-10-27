# @claude

This is Claude's dedicated branch. All changes by Claude must be made here.
Do not push directly to main. Create a Pull Request for review.

---

# https://github.com/Sovereignty-One/Grok-4.6-ChatGPT-6-Claude-5.1-Skeleton/tree/main

This repository is the full SuperGrok workspace: dashboard, bridge, backend, mobile, voice, security, and support modules all live here.

## What this repo contains

- **Unified Node backend**: `Unified_Server.js`
- **Python bridge and brain services**: `python3_bridge.py`, `bridge/`, `bus.py`, `global_brain.py`
- **Frontend/dashboard assets**: `SGHv119.html`, `FullDashboard.html`, `Sghv119-local.html`, `server_9898.js`
- **Enterprise dashboard app**: `supergrok-enterprise/`
- **iOS / Swift pieces**: `SuperGrokApp.swift`, `AppDelegate.swift`, `VoiceCommand.swift`, `SovereignMentor/`
- **Support modules and utilities**: `modules/`, `fixers/`, `selffixerai/`, `logging_utils/`, `sovereign/`, `sovereignty_ai/`
- **Security, compliance, and architecture docs**: `PORT_ARCHITECTURE.md`, `SECURITY.md`, `Compliance_Handbook.md`, `DASHBOARD_SETUP.md`

## Project structure

```text
.
├── .github/                     # CI, issues, and repo automation
├── Export/                      # Exported artifacts and generated outputs
├── Full-blocklist-main/         # Blocklist package and scripts
├── Models/                      # Model/config assets
├── Services/                    # Service layer files
├── SovereignMentor/             # App Maker Pro / SwiftUI project folder
├── Sovereignty-AI-Studio-main/  # Docker / studio deployment assets
├── Views/                       # UI view definitions
├── bridge/                      # Python bridge services
├── fixers/                      # Auto-fix helpers
├── logging_utils/               # Logging helpers
├── loggingutils/                # Legacy logging helpers
├── modules/                     # Feature modules
├── selffixerai/                 # Self-fixing analysis/security code
├── sovereign/                   # Sovereign runtime pieces
├── sovereign-bridge/            # Bridge integration docs/assets
├── sovereign_persistent_brain/  # Persistent memory scripts
├── sovereignty_ai/              # AI ratchet / guardrail logic
├── src/                         # Shared source code
├── supergrok-enterprise/        # Enterprise dashboard app
├── tests/                       # Test suite
├── Unified_Server.js            # Main Node server
├── python3_bridge.py            # Python bridge entry point
├── server_9898.js               # Dashboard/frontend server
├── Start_All.sh                 # Start all services
├── start-dashboard.sh           # Dashboard launcher
├── package.json                 # Node scripts
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Main entry points

- `npm start` → `Unified_Server.js`
- `npm run dev` → verbose unified server
- `npm run shell` → shell-enabled unified server
- `node server_9898.js` → dashboard/frontend server
- `python3 python3_bridge.py` → Python bridge
- `./Start_All.sh` → start the stack together

## Architecture notes

- Port layout is documented in `PORT_ARCHITECTURE.md`
- Dashboard setup is documented in `DASHBOARD_SETUP.md`
- Enterprise dashboard docs live in `supergrok-enterprise/README.md`
- Security and compliance notes live in `SECURITY.md` and `Compliance_Handbook.md`

## Quick start

```bash
npm install
npm start
```

For the full stack, review the architecture doc first and then launch the bridge and dashboard components as needed.

## Local CI/CD deploy + mirror

Use the local entrypoint below (no GitHub Actions required):

```bash
cp ci-cd/local/local-cicd.env.example ci-cd/local/local-cicd.env
./ci-cd/local/deploy-local.sh
```

Or run the same flow through npm:

```bash
npm run local:deploy-sync
```

What it does:
- local deploy via `docker compose`
- archives compliance exports + Merkle digests into `.local-cicd-exports/`
- prunes old archive snapshots (default keep: 10)
- pushes the checked-out branch to `Appel420/Sovereignty-AI-Studio` through the configured mirror remote (or `TARGET_BRANCH` when set)

The script fails fast with clear errors if deploy, export, or push steps fail.

## Related documentation

- `CHANGES.md`
- `MIGRATION.md`
- `UPSTREAM.md`
- `persistent-chat-client.md`
- `sovereign-production-project.md`
- `Self_Fix_AI.md`
- `Self_fixer.md`

## Notes

- This repo includes multiple subprojects, so not every folder is required for every workflow.
- Use the architecture and setup docs above when wiring new features into the stack.
