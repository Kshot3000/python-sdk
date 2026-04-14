from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from octaspace.config import ClientConfig
from octaspace.errors import APIError, OctaSpaceError
from octaspace.response import APIResponse

from .state import PlaygroundSettings

# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def response_data(value: APIResponse | OctaSpaceError | None) -> Any:
    return value.data if isinstance(value, APIResponse) else None


def response_error(value: APIResponse | OctaSpaceError | None) -> OctaSpaceError | None:
    return value if isinstance(value, OctaSpaceError) else None


def response_status(value: APIResponse | OctaSpaceError | None) -> str:
    if isinstance(value, APIResponse):
        return str(value.status_code)
    if isinstance(value, APIError):
        return str(value.status_code)
    return "—"


def response_request_id(value: APIResponse | OctaSpaceError | None) -> str:
    if isinstance(value, APIResponse):
        return value.request_id or "—"
    if isinstance(value, APIError):
        return value.request_id or "—"
    return "—"


# ---------------------------------------------------------------------------
# Node helpers
# ---------------------------------------------------------------------------

def _node_gpu_entries(node: dict[str, Any]) -> list[dict[str, Any]]:
    gpus = node.get("system", {}).get("gpus") or node.get("data", {}).get("gpus") or []
    return [item for item in gpus if isinstance(item, dict)]


def node_location(node: dict[str, Any]) -> str:
    parts = [node.get("location", {}).get("city"), node.get("location", {}).get("country")]
    rendered = ", ".join(p for p in parts if p)
    return rendered or "—"


def node_gpu_model(node: dict[str, Any]) -> str:
    entries = _node_gpu_entries(node)
    return (
        (entries[0].get("model") if entries else None)
        or node.get("system", {}).get("gpu")
        or node.get("system", {}).get("gpu_model")
        or "—"
    )


def node_gpu_count(node: dict[str, Any]) -> int:
    return len(_node_gpu_entries(node))


def node_ram_label(node: dict[str, Any]) -> str:
    ram = (
        node.get("system", {}).get("memory", {}).get("size")
        or node.get("system", {}).get("memory")
        or node.get("data", {}).get("memory_size")
        or node.get("system", {}).get("ram")
    )
    if isinstance(ram, (int, float)) and not isinstance(ram, bool) and ram > 1024:
        return f"{round(float(ram) / 1024 / 1024 / 1024)} GB"
    if ram not in (None, ""):
        return f"{ram} GB"
    return "—"


def node_summary_rows(node: dict[str, Any]) -> list[tuple[str, str]]:
    entries = _node_gpu_entries(node)
    return [
        ("State", str(node.get("state") or node.get("status") or "—")),
        ("IP", str(node.get("ip") or node.get("public_ip") or "—")),
        ("Location", node_location(node)),
        ("CPU", str(
            node.get("data", {}).get("cpu_model_name")
            or node.get("system", {}).get("cpu_model_name")
            or node.get("system", {}).get("cpu")
            or "—"
        )),
        ("Cores", str(
            node.get("data", {}).get("cpu_cores")
            or node.get("system", {}).get("cpu_cores")
            or "—"
        )),
        ("RAM", node_ram_label(node)),
        ("CUDA", str(
            node.get("data", {}).get("cuda_version")
            or node.get("system", {}).get("cuda_version")
            or "—"
        )),
        ("OS", str(
            node.get("data", {}).get("os_version")
            or node.get("system", {}).get("os")
            or "—"
        )),
        ("Driver", str(
            node.get("data", {}).get("gpu_driver_version")
            or node.get("system", {}).get("gpu_driver_version")
            or "—"
        )),
        ("Uptime", format_duration(node.get("data", {}).get("uptime") or node.get("uptime"))),
        ("GPU vendor", str(
            node.get("data", {}).get("gpu_vendor")
            or (entries[0].get("vendor") if entries else None)
            or "—"
        )),
    ]


# ---------------------------------------------------------------------------
# App helpers
# ---------------------------------------------------------------------------

def app_ports_count(app: dict[str, Any]) -> int:
    return len(app.get("ports") or []) + len(app.get("http_ports") or [])


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def session_service_label(service: Any) -> str:
    return {"mr": "RENTAL", "render": "RENDER", "vpn": "VPN"}.get(str(service), "—")


def session_service_badge_class(service: Any) -> str:
    return {
        "mr": "border border-sky-500/30 bg-sky-900/30 text-sky-400",
        "render": "border border-orange-500/30 bg-orange-900/30 text-orange-400",
        "vpn": "border border-indigo-500/30 bg-indigo-900/30 text-indigo-400",
    }.get(str(service), "border border-slate-600/40 bg-slate-700/50 text-slate-400")


def session_status_label(session: dict[str, Any], recent: bool) -> str:
    if recent and session.get("termination_reason") is not None:
        return "Normal" if int(session.get("termination_reason", 0)) in {0, 1} else "Error"
    if session.get("is_ready"):
        return "Ready"
    if session.get("progress"):
        return str(session["progress"])
    return str(session.get("status") or "Starting")


def session_status_badge_class(session: dict[str, Any], recent: bool) -> str:
    if recent and session.get("termination_reason") is not None:
        if int(session.get("termination_reason", 0)) in {0, 1}:
            return "border border-emerald-500/30 bg-emerald-500/15 text-emerald-400"
        return "border border-rose-500/30 bg-rose-500/15 text-rose-400"
    if session.get("is_ready"):
        return "border border-emerald-500/30 bg-emerald-500/15 text-emerald-400"
    return "border border-amber-500/30 bg-amber-500/15 text-amber-400"


def show_service_column(sessions: list[dict[str, Any]]) -> bool:
    return any(s.get("service") for s in sessions)


def summarize_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        sample_keys = (
            list(payload[0].keys())[:8]
            if payload and isinstance(payload[0], dict)
            else None
        )
        return {"type": "array", "count": len(payload), "sample_keys": sample_keys}
    if isinstance(payload, dict):
        return {"type": "object", "keys": list(payload.keys())[:12]}
    return {"type": type(payload).__name__, "value": payload}


# ---------------------------------------------------------------------------
# Transport / config labels
# ---------------------------------------------------------------------------

def transport_label(settings: PlaygroundSettings) -> str:
    return settings.transport_label


def transport_description(settings: PlaygroundSettings) -> str:
    return settings.transport_description


def timeout_label(settings: PlaygroundSettings) -> str:
    config = ClientConfig(api_key=settings.api_key or None, base_url=settings.base_url)
    return f"{config.open_timeout}s / {config.read_timeout}s"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def playground_present(value: Any) -> bool:
    return value is not None


def truncate_value(value: Any, leading: int = 8, trailing: int = 5) -> str:
    s = str(value)
    if len(s) <= leading + trailing + 1:
        return s
    return f"{s[:leading]}…{s[-trailing:]}"


def format_duration(value: Any) -> str:
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return "—"
    if seconds <= 0:
        return "—"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_bytes(value: Any) -> str:
    try:
        bv = float(value)
    except (TypeError, ValueError):
        return "0 B"
    if bv <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while bv >= 1024 and index < len(units) - 1:
        bv /= 1024.0
        index += 1
    return f"{bv:.1f} {units[index]}"


def format_datetime(value: Any) -> str:
    parsed = _coerce_datetime(value)
    if parsed is None:
        return value if isinstance(value, str) and value else "—"
    return parsed.astimezone().strftime("%b %-d, %H:%M")


def format_short_time(value: Any) -> str:
    parsed = _coerce_datetime(value)
    if parsed is None:
        return value if isinstance(value, str) and value else "—"
    return parsed.astimezone().strftime("%H:%M:%S")


def _coerce_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        secs = numeric / 1000.0 if numeric > 10_000_000_000 else numeric
        return datetime.fromtimestamp(secs, tz=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None
