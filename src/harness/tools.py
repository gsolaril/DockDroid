"""The tool surface and the system prompt: the model's entire world.

Six verbs, written once in JSON-schema form so the same definition can be handed
straight to a model's tool-calling API without a rewrite. Every new verb has to
earn its place: each one costs prompt tokens on every single step, forever.
"""

from __future__ import annotations

SYSTEM = """You control an Android phone through tools. You see the screen as a list of
elements, each with a stable id. Act one step at a time: choose one tool, look at
the new screen, then choose again. Never claim you did something you did not see
confirmed on screen. When the goal is reached, call done."""

TOOLS = [
    {
        "name": "tap",
        "description": "Press one button on the current screen. Use the element id from the observation.",
        "input_schema": {
            "type": "object",
            "properties": {"element": {"type": "string", "description": "element id, e.g. nav_jobs"}},
            "required": ["element"],
        },
    },
    {
        "name": "type_text",
        "description": "Replace the contents of one text field.",
        "input_schema": {
            "type": "object",
            "properties": {"element": {"type": "string"}, "text": {"type": "string"}},
            "required": ["element", "text"],
        },
    },
    {
        "name": "press",
        "description": "Physical key. key is 'back' or 'home'.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string", "enum": ["back", "home"]}},
            "required": ["key"],
        },
    },
    {
        "name": "scroll",
        "description": "Scroll the current list. direction is 'up' or 'down'.",
        "input_schema": {
            "type": "object",
            "properties": {"direction": {"type": "string", "enum": ["up", "down"]}},
            "required": ["direction"],
        },
    },
    {
        "name": "observe",
        "description": "Look at the screen again without acting.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "done",
        "description": "End the episode. Only call this when the screen shows the goal is reached.",
        "input_schema": {
            "type": "object",
            "properties": {"summary": {"type": "string", "description": "one line: what is now true"}},
            "required": ["summary"],
        },
    },
]
