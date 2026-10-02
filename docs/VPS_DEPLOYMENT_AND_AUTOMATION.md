# VPS Deployment and Automation

## Target
Host alias: `bmv-neuro-lab`
Target path: `/home/ljamtz/options-system`

## Security boundary
`.env` is never included in deployment bundles.
Alpaca credentials must exist only on the VPS at `/home/ljamtz/options-system/.env` with restrictive permissions.

## Services
`options-intraday-collector.service`
- multi-asset options snapshots
- market-clock gated
- research only

`options-spy-collector.service`
- SPY prospective Market State snapshots
- O3/O6 research state

`options-postclose.service`
- rebuilds prospective dataset
- labels completed H1/H3
- rebuilds intraday dataset v2
- updates scoreboard and daily report
## Timers
- Intraday collector: every 5 minutes from boot; collector itself skips closed market.
- SPY collector: every 5 minutes from boot; collector itself skips closed market.
- Post-close pipeline: 23:30 UTC daily, safely after US regular close in both DST regimes.

## Deployment
Local helper: `scripts/deploy_vps.ps1`
Installer on VPS: `deploy/scripts/install_vps.sh`

Recommended sequence:
1. Unlock the local Hetzner SSH key in `ssh-agent`.
2. Run `scripts/deploy_vps.ps1 -IncludeData` if historical/prospective data should also be seeded.
3. Create/verify the VPS `.env`; do not copy it into git or bundles.
4. Run `chmod 700 deploy/scripts/install_vps.sh && deploy/scripts/install_vps.sh`.
5. Verify `systemctl list-timers 'options-*'` and service logs with `journalctl`.

## Current deployment blocker
The VPS is reachable on Tailscale port 22, but the local `id_ed25519_hetzner` key is passphrase-encrypted and not loaded in the Windows ssh-agent. No passphrase is stored or requested by this project.

## Cutover rule
Keep Windows collectors enabled until the VPS has produced and indexed at least one valid market-open snapshot for both SPY and the intraday universe.
After verification, run `scripts/disable_local_collectors_after_vps.ps1` locally to prevent duplicate collection.
Do not disable the laptop tasks before VPS verification.
