#!/usr/bin/env python3
"""Render a static, accessible teaching diagram without third-party packages."""

from __future__ import annotations

import argparse
import html
import math
import re
import textwrap
import unicodedata
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


def parts(value: str, count: int, label: str) -> list[str]:
    result = value.split("|", count - 1)
    if len(result) != count:
        raise ValueError(f"{label} must contain {count} pipe-separated fields: {value!r}")
    return [item.strip() for item in result]


def display_width(value: str) -> int:
    return sum(2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in value)


def wrap_label(value: str, limit: int = 22) -> list[str]:
    value = " ".join(value.split())
    if not value:
        return [""]
    if " " in value:
        return textwrap.wrap(value, width=limit, break_long_words=True)[:3]
    lines: list[str] = []
    current = ""
    for char in value:
        if current and display_width(current + char) > limit:
            lines.append(current)
            current = char
        else:
            current += char
    if current:
        lines.append(current)
    return lines[:3]


def parse_nodes(values: list[str]) -> list[dict[str, str]]:
    nodes = []
    for value in values:
        node_id, label, detail = parts(value, 3, "--node")
        if not ID_RE.match(node_id):
            raise ValueError(f"invalid node ID: {node_id!r}")
        nodes.append({"id": node_id, "label": label, "detail": detail})
    if not 2 <= len(nodes) <= 10:
        raise ValueError("provide between 2 and 10 nodes")
    if len({node["id"] for node in nodes}) != len(nodes):
        raise ValueError("node IDs must be unique")
    return nodes


def parse_edges(values: list[str], node_ids: set[str]) -> list[dict[str, str]]:
    edges = []
    for value in values:
        source, target, label = parts(value, 3, "--edge")
        if source not in node_ids or target not in node_ids:
            raise ValueError(f"edge refers to unknown node: {source!r} -> {target!r}")
        edges.append({"from": source, "to": target, "label": label})
    return edges


def flow_positions(count: int) -> tuple[int, int, list[tuple[float, float]]]:
    if count <= 4:
        width, height = 1180, 430
        gap = (width - 280) / max(1, count - 1)
        return width, height, [(140 + index * gap, 235) for index in range(count)]
    width, height = 960, 210 + count * 155
    return width, height, [(width / 2, 180 + index * 150) for index in range(count)]


def cycle_positions(count: int) -> tuple[int, int, list[tuple[float, float]]]:
    width, height = 900, 760
    radius = 245
    return width, height, [
        (width / 2 + radius * math.cos(-math.pi / 2 + 2 * math.pi * index / count),
         390 + radius * math.sin(-math.pi / 2 + 2 * math.pi * index / count))
        for index in range(count)
    ]


def compare_positions(count: int) -> tuple[int, int, list[tuple[float, float]]]:
    left_count = (count + 1) // 2
    right_count = count - left_count
    rows = max(left_count, right_count)
    width, height = 1040, 230 + rows * 165
    positions = [(280, 190 + index * 160) for index in range(left_count)]
    positions.extend((760, 190 + index * 160) for index in range(right_count))
    return width, height, positions


def hierarchy_positions(nodes: list[dict[str, str]], edges: list[dict[str, str]]) -> tuple[int, int, list[tuple[float, float]]]:
    indegree = {node["id"]: 0 for node in nodes}
    children: dict[str, list[str]] = {node["id"]: [] for node in nodes}
    for edge in edges:
        indegree[edge["to"]] += 1
        children[edge["from"]].append(edge["to"])
    roots = [node["id"] for node in nodes if indegree[node["id"]] == 0]
    rank = {node_id: 0 for node_id in roots}
    queue = list(roots)
    remaining_indegree = dict(indegree)
    while queue:
        current = queue.pop(0)
        for child in children[current]:
            rank[child] = max(rank.get(child, 0), rank[current] + 1)
            remaining_indegree[child] -= 1
            if remaining_indegree[child] == 0:
                queue.append(child)
    # Cyclic or disconnected leftovers are placed on one final level instead of
    # letting a malformed hierarchy create an unbounded ranking loop.
    for node in nodes:
        rank.setdefault(node["id"], max(rank.values(), default=0) + 1)
    levels: dict[int, list[str]] = {}
    for node in nodes:
        levels.setdefault(rank[node["id"]], []).append(node["id"])
    width = max(900, max(len(items) for items in levels.values()) * 300)
    height = 250 + len(levels) * 180
    by_id: dict[str, tuple[float, float]] = {}
    for level, ids in sorted(levels.items()):
        gap = width / (len(ids) + 1)
        for index, node_id in enumerate(ids):
            by_id[node_id] = (gap * (index + 1), 180 + level * 175)
    return width, height, [by_id[node["id"]] for node in nodes]


def node_svg(node: dict[str, str], x: float, y: float) -> str:
    label_lines = wrap_label(node["label"], 20)
    detail_lines = wrap_label(node["detail"], 34)
    height = 78 + 20 * len(label_lines) + 17 * len(detail_lines)
    top = y - height / 2
    lines = [f'<g id="node-{html.escape(node["id"])}">', f'<rect x="{x - 130:.1f}" y="{top:.1f}" width="260" height="{height:.1f}" rx="18" fill="#FFFDF8" stroke="#24445C" stroke-width="2"/>']
    label_y = top + 34
    for index, line in enumerate(label_lines):
        lines.append(f'<text x="{x:.1f}" y="{label_y + index * 20:.1f}" class="node-label">{html.escape(line)}</text>')
    detail_y = label_y + len(label_lines) * 20 + 11
    for index, line in enumerate(detail_lines):
        lines.append(f'<text x="{x:.1f}" y="{detail_y + index * 17:.1f}" class="node-detail">{html.escape(line)}</text>')
    lines.append("</g>")
    return "\n".join(lines)


def render(kind: str, title: str, description: str, nodes: list[dict[str, str]], edges: list[dict[str, str]]) -> str:
    if kind == "flow":
        width, height, positions = flow_positions(len(nodes))
    elif kind == "cycle":
        width, height, positions = cycle_positions(len(nodes))
    elif kind == "compare":
        width, height, positions = compare_positions(len(nodes))
    else:
        width, height, positions = hierarchy_positions(nodes, edges)
    position = {node["id"]: positions[index] for index, node in enumerate(nodes)}
    body = []
    for edge in edges:
        x1, y1 = position[edge["from"]]
        x2, y2 = position[edge["to"]]
        dx, dy = x2 - x1, y2 - y1
        distance = max(1.0, math.hypot(dx, dy))
        start_x, start_y = x1 + dx / distance * 135, y1 + dy / distance * 70
        end_x, end_y = x2 - dx / distance * 145, y2 - dy / distance * 75
        body.append(f'<line x1="{start_x:.1f}" y1="{start_y:.1f}" x2="{end_x:.1f}" y2="{end_y:.1f}" class="edge" marker-end="url(#arrow)"/>')
        if edge["label"]:
            body.append(f'<text x="{(x1 + x2) / 2:.1f}" y="{(y1 + y2) / 2 - 8:.1f}" class="edge-label">{html.escape(edge["label"])}</text>')
    body.extend(node_svg(node, *position[node["id"]]) for node in nodes)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="diagram-title diagram-desc">
<title id="diagram-title">{html.escape(title)}</title>
<desc id="diagram-desc">{html.escape(description)}</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#C45532"/></marker></defs>
<style>.bg{{fill:#F4F0E8}}.title{{font:700 28px system-ui,sans-serif;fill:#172A38;text-anchor:middle}}.node-label{{font:700 17px system-ui,sans-serif;fill:#172A38;text-anchor:middle}}.node-detail{{font:14px system-ui,sans-serif;fill:#415868;text-anchor:middle}}.edge{{stroke:#C45532;stroke-width:3;fill:none}}.edge-label{{font:600 13px system-ui,sans-serif;fill:#8A351E;text-anchor:middle;paint-order:stroke;stroke:#F4F0E8;stroke-width:5}}</style>
<rect class="bg" width="100%" height="100%" rx="20"/>
<text x="{width / 2:.1f}" y="52" class="title">{html.escape(title)}</text>
{''.join(body)}
</svg>\n'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a safe, accessible SVG learning diagram.")
    parser.add_argument("--kind", choices=["flow", "cycle", "compare", "hierarchy"], required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--node", action="append", required=True, help="id|label|detail")
    parser.add_argument("--edge", action="append", default=[], help="source-id|target-id|label")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    nodes = parse_nodes(args.node)
    edges = parse_edges(args.edge, {node["id"] for node in nodes})
    if args.kind in {"flow", "cycle", "hierarchy"} and not edges:
        edges = [
            {"from": nodes[index]["id"], "to": nodes[(index + 1) % len(nodes)]["id"], "label": ""}
            for index in range(len(nodes) if args.kind == "cycle" else len(nodes) - 1)
        ]
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(args.kind, args.title, args.description, nodes, edges), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
