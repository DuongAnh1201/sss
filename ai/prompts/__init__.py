"""Prompt loading helpers.

Every agent's system prompt lives as a Markdown file in this directory
(e.g. ``orchestrator.md``). Agents load them with ``load_prompt("orchestrator")``.
"""
from functools import lru_cache
from pathlib import Path

_PROMPT_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    """Return the text of ``ai/prompts/<name>.md``.

    Args:
        name: Prompt file stem, without the ``.md`` extension.

    Raises:
        FileNotFoundError: if no matching prompt file exists.
    """
    path = _PROMPT_DIR / f"{name}.md"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in _PROMPT_DIR.glob("*.md")))
        raise FileNotFoundError(
            f"Prompt '{name}' not found at {path}. Available: {available or '(none)'}"
        )
    return path.read_text(encoding="utf-8")
