"""Observation rendering: turning phone state into text a model can read.

Observation design is the highest-leverage decision in an agent system (module
4). This version is deliberately naive: every element, no filtering, no ranking,
no compression. We need a baseline before we are allowed to improve it.
"""

from __future__ import annotations

import json

from ..models.episode import Step


def render(obs: dict) -> str:
    lines = [f"SCREEN: {obs['screen']}"]
    if obs.get("toast"):
        lines.append(f"NOTE: {obs['toast']}")
    lines.append("ELEMENTS:")
    for el in obs["elements"]:
        value = f'  value="{el["value"]}"' if el.get("value") else ""
        lines.append(f'  {el["id"]:<16} {el["role"]:<7} "{el["text"]}"{value}')
    return "\n".join(lines)


def approx_tokens(text: str) -> int:
    """Cheap token estimate: ~4 characters per token for English.

    Good enough to compare two prompts. Not good enough to predict an invoice.
    It exists because lesson 0.1 must run with no API key; real `usage` numbers
    replace it the moment a model is in the loop.
    """
    return max(1, len(text) // 4)


def history_text(steps: list[Step]) -> str:
    if not steps:
        return "(nothing yet)"
    lines = []
    for s in steps:
        action = json.dumps(s.action, ensure_ascii=False) if s.action else "{}"
        outcome = f"ERROR: {s.error}" if s.error else s.result
        lines.append(f"{s.n}. {action} -> {outcome}")
    return "\n".join(lines)
