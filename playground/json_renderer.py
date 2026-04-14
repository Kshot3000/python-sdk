from __future__ import annotations

import json
from typing import Any

from markupsafe import Markup, escape

from octaspace.response import APIResponse

from .errors import error_payload


def serializable(value: Any) -> Any:
    if isinstance(value, APIResponse):
        return serializable(value.data)
    if isinstance(value, Exception):
        return error_payload(value)
    if isinstance(value, dict):
        return {str(k): serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "to_dict"):
        return serializable(value.to_dict())
    return str(value)


def json_html(value: Any) -> Markup:
    return _render_node(serializable(value), 0)


def _render_node(node: Any, level: int) -> Markup:
    if isinstance(node, dict):
        return _render_hash(node, level)
    if isinstance(node, list):
        return _render_array(node, level)
    if isinstance(node, str):
        return Markup(f'<span class="json-string">{escape(json.dumps(node))}</span>')
    if isinstance(node, bool):
        return Markup(f'<span class="json-bool">{escape(str(node).lower())}</span>')
    if isinstance(node, (int, float)):
        return Markup(f'<span class="json-number">{escape(str(node))}</span>')
    if node is None:
        return Markup('<span class="json-null">null</span>')
    return Markup(f'<span class="json-string">{escape(json.dumps(str(node)))}</span>')


def _render_hash(node: dict[str, Any], level: int) -> Markup:
    if not node:
        return Markup("{}")
    lines = [
        f'{_indent(level + 1)}<span class="json-key">{escape(json.dumps(str(k)))}</span>: '
        f"{_render_node(v, level + 1)}"
        for k, v in node.items()
    ]
    return Markup("{\n" + ",\n".join(lines) + f"\n{_indent(level)}}}")


def _render_array(node: list[Any], level: int) -> Markup:
    if not node:
        return Markup("[]")
    lines = [f"{_indent(level + 1)}{_render_node(item, level + 1)}" for item in node]
    return Markup("[\n" + ",\n".join(lines) + f"\n{_indent(level)}]")


def _indent(level: int) -> str:
    return "  " * level
