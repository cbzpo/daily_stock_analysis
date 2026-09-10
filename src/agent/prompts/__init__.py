# -*- coding: utf-8 -*-
"""
Prompt utilities — loads the shared dashboard schema for embedding in prompts.
"""

import json
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent
_SCHEMA_PATH = _PROMPTS_DIR / "dashboard_schema.json"
_schema_cache: str = ""


def get_dashboard_schema_for_prompt() -> str:
    """Return the dashboard JSON schema as a Python f-string-safe block.

    The schema is loaded once from ``dashboard_schema.json`` and cached.
    Double braces (``{{`` / ``}}``) are escaped so that embedding this
    string inside an f-string template does not trigger interpolation.
    """
    global _schema_cache
    if _schema_cache:
        return _schema_cache

    raw = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    # Re-serialize with 4-space indent for readability in prompts
    formatted = json.dumps(raw, ensure_ascii=False, indent=4)
    # Escape braces for f-string embedding: { -> {{ , } -> }}
    _schema_cache = formatted.replace("{", "{{").replace("}", "}}")
    return _schema_cache
