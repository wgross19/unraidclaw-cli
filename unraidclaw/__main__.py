"""UnraidClaw CLI — Command-line interface for managing Unraid servers via UnraidClaw.

Usage:
  export UNRAIDCLAW_URL=https://tower:9876
  export UNRAIDCLAW_KEY=your-api-key
  export UNRAIDCLAW_TLS_SKIP=1       # if using self-signed cert

  unraidclaw health
  unraidclaw docker list
  unraidclaw docker info <id>
  unraidclaw docker logs <id>
  unraidclaw docker start|stop|restart|pause|unpause <id>
  unraidclaw docker create --image nginx:latest --name my-nginx ...
  unraidclaw docker rm <id> [--force]
  unraidclaw vm list
  unraidclaw vm info <id>
  unraidclaw vm start|stop|force-stop|pause|resume|reboot|reset <id>
  unraidclaw vm rm <id>
  unraidclaw array status
  unraidclaw array parity-status
  unraidclaw array start|stop
  unraidclaw array parity-start|parity-pause|parity-resume|parity-cancel
  unraidclaw disk list
  unraidclaw disk info <name>
  unraidclaw share list
  unraidclaw share info <name>
  unraidclaw share update <name> [--comment ...] [--allocator ...] [--floor ...] [--split-level ...]
  unraidclaw system info
  unraidclaw system metrics
  unraidclaw system services
  unraidclaw system reboot|shutdown
  unraidclaw notify list [--type UNREAD|ARCHIVED|ALL] [--limit N] [--offset N]
  unraidclaw notify overview
  unraidclaw notify create <title> <subject> <description> [--importance normal|warning|alert]
  unraidclaw notify archive <id>
  unraidclaw notify rm <id>
  unraidclaw network
  unraidclaw user me
  unraidclaw log syslog [--lines N]
"""

import argparse
import sys

from . import client, output


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    try:
        result = args.func(args)
    except client.UnraidAPIError as e:
        output.die(str(e))

    if result is not None:
        fmt = getattr(args, "output", "table")
        print(output.format_output(result, fmt))


# ── Top-level args ──────────────────────────────────────────────

def _build_parser():
    p = argparse.ArgumentParser(description="UnraidClaw CLI")
    p.add_argument("--url", help="Override UNRAIDCLAW_URL")
    p.add_argument("--key", help="Override UNRAIDCLAW_KEY")
    p.add_argument("--tls-skip", action="store_true", help="Skip TLS verification")
    p.add_argument("--output", choices=["json", "table"], default="table")
    p.add_argument("--version", action="version", version=f"unraidclaw {__import__('unraidclaw').__version__}")

    sub = p.add_subparsers(dest="command")

    _health(sub)
    _docker(sub)
    _vm(sub)
    _array(sub)
    _disk(sub)
    _share(sub)
    _system(sub)
    _notify(sub)
    _network(sub)
    _user(sub)
    _log(sub)

    return p


def _apply_env_overrides(args):
    """Apply --url / --key / --tls-skip overrides to environment."""
    if hasattr(args, "url") and args.url:
        import os
        os.environ["UNRAIDCLAW_URL"] = args.url
    if hasattr(args, "key") and args.key:
        import os
        os.environ["UNRAIDCLAW_KEY"] = args.key
    if hasattr(args, "tls_skip") and args.tls_skip:
        import os
        os.environ["UNRAIDCLAW_TLS_SKIP"] = "1"


# ═══════════════════════════════════════════════════════════════
# Health
# ═══════════════════════════════════════════════════════════════

def _health(sub):
    p = sub.add_parser("health", help="Check server health")
    p.set_defaults(func=_cmd_health)


def _cmd_health(args):
    _apply_env_overrides(args)
    return client.get("/api/health")


# ═══════════════════════════════════════════════════════════════
# Docker
# ═══════════════════════════════════════════════════════════════

def _docker(sub):
    d = sub.add_parser("docker", help="Manage Docker containers")
    ds = d.add_subparsers(dest="docker_action")

    ds.add_parser("list", help="List containers").set_defaults(func=_cmd_docker_list)

    info = ds.add_parser("info", help="Get container details")
    info.add_argument("id")
    info.set_defaults(func=_cmd_docker_info)

    logs = ds.add_parser("logs", help="Get container logs")
    logs.add_argument("id")
    logs.add_argument("--tail", default="100")
    logs.add_argument("--since")
    logs.set_defaults(func=_cmd_docker_logs)

    for action in ("start", "stop", "restart", "pause", "unpause"):
        ap = ds.add_parser(action, help=f"{action.capitalize()} container")
        ap.add_argument("id")
        ap.set_defaults(func=_make_docker_action(action))

    create = ds.add_parser("create", help="Create a container")
    create.add_argument("--image", required=True, help="Docker image (e.g. nginx:latest)")
    create.add_argument("--name", help="Container name")
    create.add_argument("--port", action="append", dest="ports", default=[], help="Port mapping (host:container[/tcp|udp])")
    create.add_argument("--volume", action="append", dest="volumes", default=[], help="Volume mapping (/host:/container[:ro|rw])")
    create.add_argument("--env", action="append", dest="env", default=[], help="Environment var (KEY=VALUE)")
    create.add_argument("--restart", choices=["no", "always", "unless-stopped", "on-failure"], default="unless-stopped")
    create.add_argument("--network", default="bridge")
    create.add_argument("--label", action="append", dest="labels", default=[], help="Custom labels (key=value)")
    create.add_argument("--icon", help="Unraid icon URL")
    create.add_argument("--webui", help="WebUI URL")
    create.set_defaults(func=_cmd_docker_create)

    rm = ds.add_parser("rm", help="Remove container")
    rm.add_argument("id")
    rm.add_argument("--force", action="store_true")
    rm.set_defaults(func=_cmd_docker_rm)


def _make_docker_action(action):
    def cmd(args):
        _apply_env_overrides(args)
        return client.post(f"/api/docker/containers/{args.id}/{action}")
    return cmd


def _cmd_docker_list(args):
    _apply_env_overrides(args)
    return client.get("/api/docker/containers")


def _cmd_docker_info(args):
    _apply_env_overrides(args)
    return client.get(f"/api/docker/containers/{args.id}")


def _cmd_docker_logs(args):
    _apply_env_overrides(args)
    q = {"tail": args.tail}
    if args.since:
        q["since"] = args.since
    return client.get(f"/api/docker/containers/{args.id}/logs", q)


def _cmd_docker_create(args):
    _apply_env_overrides(args)
    body = {
        "image": args.image,
        "ports": args.ports,
        "volumes": args.volumes,
        "env": args.env,
        "restart": args.restart,
        "network": args.network,
    }
    if args.name:
        body["name"] = args.name
    if args.labels:
        labels = {}
        for lv in args.labels:
            k, _, v = lv.partition("=")
            labels[k] = v
        body["labels"] = labels
    if args.icon:
        body["icon"] = args.icon
    if args.webui:
        body["webui"] = args.webui
    return client.post("/api/docker/containers", body)


def _cmd_docker_rm(args):
    _apply_env_overrides(args)
    path = f"/api/docker/containers/{args.id}"
    if args.force:
        path += "?force=true"
    return client.delete(path)


# ═══════════════════════════════════════════════════════════════
# VMs
# ═══════════════════════════════════════════════════════════════

def _vm(sub):
    v = sub.add_parser("vm", help="Manage virtual machines")
    vs = v.add_subparsers(dest="vm_action")

    vs.add_parser("list", help="List VMs").set_defaults(func=_cmd_vm_list)

    info = vs.add_parser("info", help="Get VM details")
    info.add_argument("id")
    info.set_defaults(func=_cmd_vm_info)

    for action in ("start", "stop", "force-stop", "pause", "resume", "reboot", "reset"):
        ap = vs.add_parser(action, help=f"{action.replace('-', ' ').title()} VM")
        ap.add_argument("id")
        ap.set_defaults(func=_make_vm_action(action.replace("-", "_")))

    rm = vs.add_parser("rm", help="Remove VM")
    rm.add_argument("id")
    rm.set_defaults(func=_cmd_vm_rm)


VIRSH_PATH_MAP = {
    "start": "start", "stop": "stop", "force_stop": "force-stop",
    "pause": "pause", "resume": "resume", "reboot": "reboot", "reset": "reset",
}


def _make_vm_action(action):
    api_path = VIRSH_PATH_MAP.get(action, action)
    def cmd(args):
        _apply_env_overrides(args)
        return client.post(f"/api/vms/{args.id}/{api_path}")
    return cmd


def _cmd_vm_list(args):
    _apply_env_overrides(args)
    return client.get("/api/vms")


def _cmd_vm_info(args):
    _apply_env_overrides(args)
    return client.get(f"/api/vms/{args.id}")


def _cmd_vm_rm(args):
    _apply_env_overrides(args)
    return client.delete(f"/api/vms/{args.id}")


# ═══════════════════════════════════════════════════════════════
# Array
# ═══════════════════════════════════════════════════════════════

def _array(sub):
    a = sub.add_parser("array", help="Manage Unraid array")
    sa = a.add_subparsers(dest="array_action")

    sa.add_parser("status", help="Array status").set_defaults(func=_cmd_array_status)
    sa.add_parser("parity-status", help="Parity check status").set_defaults(func=_cmd_parity_status)
    sa.add_parser("start", help="Start array").set_defaults(func=_cmd_array_start)
    sa.add_parser("stop", help="Stop array").set_defaults(func=_cmd_array_stop)

    ps = sa.add_parser("parity-start", help="Start parity check")
    ps.add_argument("--correct", action="store_true", help="Correct parity errors")
    ps.set_defaults(func=_cmd_parity_start)

    for act in ("parity-pause", "parity-resume", "parity-cancel"):
        sa.add_parser(act, help=act.replace("-", " ").title()).set_defaults(
            func=_make_array_action(act.replace("-", "_"))
        )


def _cmd_array_status(args):
    _apply_env_overrides(args)
    return client.get("/api/array/status")


def _cmd_parity_status(args):
    _apply_env_overrides(args)
    return client.get("/api/array/parity/status")


def _cmd_array_start(args):
    _apply_env_overrides(args)
    return client.post("/api/array/start")


def _cmd_array_stop(args):
    _apply_env_overrides(args)
    return client.post("/api/array/stop")


def _cmd_parity_start(args):
    _apply_env_overrides(args)
    return client.post("/api/array/parity/start", {"correct": args.correct})


def _make_array_action(action):
    api_path = action.replace("_", "/")
    def cmd(args):
        _apply_env_overrides(args)
        return client.post(f"/api/array/{api_path}")
    return cmd


# ═══════════════════════════════════════════════════════════════
# Disks
# ═══════════════════════════════════════════════════════════════

def _disk(sub):
    d = sub.add_parser("disk", help="Manage disks")
    ds = d.add_subparsers(dest="disk_action")

    ds.add_parser("list", help="List disks").set_defaults(func=_cmd_disk_list)

    info = ds.add_parser("info", help="Disk details")
    info.add_argument("id", help="Disk name (disk1, cache, parity, etc.)")
    info.set_defaults(func=_cmd_disk_info)


def _cmd_disk_list(args):
    _apply_env_overrides(args)
    return client.get("/api/disks")


def _cmd_disk_info(args):
    _apply_env_overrides(args)
    return client.get(f"/api/disks/{args.id}")


# ═══════════════════════════════════════════════════════════════
# Shares
# ═══════════════════════════════════════════════════════════════

def _share(sub):
    s = sub.add_parser("share", help="Manage shares")
    ss = s.add_subparsers(dest="share_action")

    ss.add_parser("list", help="List shares").set_defaults(func=_cmd_share_list)

    info = ss.add_parser("info", help="Share details")
    info.add_argument("name")
    info.set_defaults(func=_cmd_share_info)

    upd = ss.add_parser("update", help="Update share settings")
    upd.add_argument("name")
    upd.add_argument("--comment")
    upd.add_argument("--allocator", choices=["highwater", "fill", "most-free"])
    upd.add_argument("--floor", type=int, help="Min free space (KiB)")
    upd.add_argument("--split-level", type=int, dest="split_level")
    upd.set_defaults(func=_cmd_share_update)


def _cmd_share_list(args):
    _apply_env_overrides(args)
    return client.get("/api/shares")


def _cmd_share_info(args):
    _apply_env_overrides(args)
    return client.get(f"/api/shares/{args.name}")


def _cmd_share_update(args):
    _apply_env_overrides(args)
    body = {}
    if args.comment is not None:
        body["comment"] = args.comment
    if args.allocator is not None:
        body["allocator"] = args.allocator
    if args.floor is not None:
        body["floor"] = str(args.floor)
    if args.split_level is not None:
        body["splitLevel"] = str(args.split_level)
    return client.patch(f"/api/shares/{args.name}", body)


# ═══════════════════════════════════════════════════════════════
# System
# ═══════════════════════════════════════════════════════════════

def _system(sub):
    s = sub.add_parser("system", help="System operations")
    ss = s.add_subparsers(dest="system_action")

    ss.add_parser("info", help="System info (OS, CPU, memory, load)").set_defaults(func=_cmd_system_info)
    ss.add_parser("metrics", help="Live metrics (memory, CPU load)").set_defaults(func=_cmd_system_metrics)
    ss.add_parser("services", help="List services").set_defaults(func=_cmd_system_services)

    sa = ss.add_parser("reboot", help="Reboot the server")
    sa.add_argument("--yes", action="store_true", required=True, help="Confirm reboot")
    sa.set_defaults(func=_cmd_system_reboot)

    sd = ss.add_parser("shutdown", help="Shutdown the server")
    sd.add_argument("--yes", action="store_true", required=True, help="Confirm shutdown")
    sd.set_defaults(func=_cmd_system_shutdown)


def _cmd_system_info(args):
    _apply_env_overrides(args)
    return client.get("/api/system/info")


def _cmd_system_metrics(args):
    _apply_env_overrides(args)
    return client.get("/api/system/metrics")


def _cmd_system_services(args):
    _apply_env_overrides(args)
    return client.get("/api/system/services")


def _cmd_system_reboot(args):
    _apply_env_overrides(args)
    return client.post("/api/system/reboot")


def _cmd_system_shutdown(args):
    _apply_env_overrides(args)
    return client.post("/api/system/shutdown")


# ═══════════════════════════════════════════════════════════════
# Notifications
# ═══════════════════════════════════════════════════════════════

def _notify(sub):
    n = sub.add_parser("notify", help="Manage notifications")
    ns = n.add_subparsers(dest="notify_action")

    lst = ns.add_parser("list", help="List notifications")
    lst.add_argument("--type", choices=["UNREAD", "ARCHIVED", "ALL"], default="UNREAD")
    lst.add_argument("--limit", type=int, default=50)
    lst.add_argument("--offset", type=int, default=0)
    lst.set_defaults(func=_cmd_notify_list)

    ns.add_parser("overview", help="Notification counts").set_defaults(func=_cmd_notify_overview)

    cr = ns.add_parser("create", help="Create notification")
    cr.add_argument("title")
    cr.add_argument("subject")
    cr.add_argument("description")
    cr.add_argument("--importance", choices=["normal", "warning", "alert"], default="normal")
    cr.set_defaults(func=_cmd_notify_create)

    ar = ns.add_parser("archive", help="Archive notification")
    ar.add_argument("id")
    ar.set_defaults(func=_cmd_notify_archive)

    rm = ns.add_parser("rm", help="Delete notification")
    rm.add_argument("id")
    rm.set_defaults(func=_cmd_notify_rm)


def _cmd_notify_list(args):
    _apply_env_overrides(args)
    return client.get("/api/notifications", {"type": args.type, "limit": str(args.limit), "offset": str(args.offset)})


def _cmd_notify_overview(args):
    _apply_env_overrides(args)
    return client.get("/api/notifications/overview")


def _cmd_notify_create(args):
    _apply_env_overrides(args)
    return client.post("/api/notifications", {
        "title": args.title,
        "subject": args.subject,
        "description": args.description,
        "importance": args.importance,
    })


def _cmd_notify_archive(args):
    _apply_env_overrides(args)
    return client.post(f"/api/notifications/{args.id}/archive")


def _cmd_notify_rm(args):
    _apply_env_overrides(args)
    return client.delete(f"/api/notifications/{args.id}")


# ═══════════════════════════════════════════════════════════════
# Network
# ═══════════════════════════════════════════════════════════════

def _network(sub):
    p = sub.add_parser("network", help="Network info (interfaces, routes, DNS)")
    p.set_defaults(func=_cmd_network)


def _cmd_network(args):
    _apply_env_overrides(args)
    return client.get("/api/network")


# ═══════════════════════════════════════════════════════════════
# Users
# ═══════════════════════════════════════════════════════════════

def _user(sub):
    u = sub.add_parser("user", help="User info")
    us = u.add_subparsers(dest="user_action")
    us.add_parser("me", help="Current user info").set_defaults(func=_cmd_user_me)


def _cmd_user_me(args):
    _apply_env_overrides(args)
    return client.get("/api/users/me")


# ═══════════════════════════════════════════════════════════════
# Logs
# ═══════════════════════════════════════════════════════════════

def _log(sub):
    l = sub.add_parser("log", help="View logs")
    ls = l.add_subparsers(dest="log_action")
    sl = ls.add_parser("syslog", help="View syslog")
    sl.add_argument("--lines", type=int, default=50, help="Number of lines (1-1000, default 50)")
    sl.set_defaults(func=_cmd_log_syslog)


def _cmd_log_syslog(args):
    _apply_env_overrides(args)
    return client.get("/api/logs/syslog", {"lines": str(args.lines)})


# ── Entry point ─────────────────────────────────────────────────

if __name__ == "__main__":
    main()
