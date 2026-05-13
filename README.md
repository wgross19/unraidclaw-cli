# UnraidClaw CLI

[![repo](https://img.shields.io/badge/repo-wgross19/unraidclaw--cli-blue)](https://github.com/wgross19/unraidclaw-cli)

Command-line interface for the [UnraidClaw](https://github.com/emaspa/unraidclaw) AI Agent Gateway — control your Unraid server from the terminal or any AI agent.

## Requirements

- **Unraid 7.0+** with the [UnraidClaw plugin](https://github.com/emaspa/unraidclaw) installed and running on port 9876
- **Python ≥3.10** (stdlib only, zero pip deps)

## Install

```bash
# Direct from GitHub
pip install git+https://github.com/wgross19/unraidclaw-cli.git

# Clone + install locally
git clone https://github.com/wgross19/unraidclaw-cli.git
cd unraidclaw-cli
pip install .

# Or in development mode (editable)
pip install -e .
```

## Configure

```bash
export UNRAIDCLAW_URL=https://tower.local:9876
export UNRAIDCLAW_KEY=your-unraidclaw-api-key
export UNRAIDCLAW_TLS_SKIP=1          # if using self-signed cert
```

Or pass per-command:

```bash
unraidclaw --url https://tower:9876 --key abc123 --tls-skip health
```

## Usage

```
unraidclaw health                         # Server health check

# Docker
unraidclaw docker list                    # All containers
unraidclaw docker info <id>               # Container details (ports, mounts)
unraidclaw docker logs <id>               # Container logs
unraidclaw docker start|stop|restart|pause|unpause <id>
unraidclaw docker create --image nginx:latest --name my-nginx --port 8080:80
unraidclaw docker rm <id> [--force]

# VMs
unraidclaw vm list                        # All VMs
unraidclaw vm info <id>
unraidclaw vm start|stop|force-stop|pause|resume|reboot|reset <id>
unraidclaw vm rm <id>

# Array
unraidclaw array status                   # Array health, disks, capacity
unraidclaw array parity-status            # Running parity check progress
unraidclaw array start|stop
unraidclaw array parity-start [--correct]
unraidclaw array parity-pause|parity-resume|parity-cancel

# Disks
unraidclaw disk list                      # All disks with usage / SMART
unraidclaw disk info <name>               # Single disk (e.g. disk1, parity)

# Shares
unraidclaw share list
unraidclaw share info <name>
unraidclaw share update <name> --comment "media" --allocator highwater

# System
unraidclaw system info                    # OS, CPU, memory, load
unraidclaw system metrics                 # Live CPU/memory
unraidclaw system services                # Running services
unraidclaw system reboot --yes
unraidclaw system shutdown --yes

# Notifications
unraidclaw notify list [--type UNREAD]
unraidclaw notify overview
unraidclaw notify create "Title" "Subject" "Details" [--importance warning]
unraidclaw notify archive <id>
unraidclaw notify rm <id>

# Other
unraidclaw network                        # Interfaces, routes, DNS
unraidclaw user me                        # Current user
unraidclaw log syslog [--lines 100]       # Tail syslog
```

## Output formats

```bash
unraidclaw --output json docker list      # Machine-readable JSON
unraidclaw --output table docker list     # Human-readable table (default)
```

## Zero dependencies

Uses only Python stdlib: `urllib`, `json`, `argparse`, `ssl`. No pip install requirements beyond Python ≥3.10.
