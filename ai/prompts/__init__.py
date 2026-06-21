"""Prompt loading helpers.

Every agent's system prompt lives as a Markdown file in this directory
(e.g. ``orchestrator.md``). Agents load them with ``load_prompt("orchestrator")``.

Assistant identity / voice / behavior rules live in ``doc/SOUL.md`` — load with
``load_soul()`` for runtime injection into the orchestrator.
"""
from functools import lru_cache
from pathlib import Path

_PROMPT_DIR = Path(__file__).parent
_REPO_ROOT = _PROMPT_DIR.parents[1]
_SOUL_PATH = _REPO_ROOT / "doc" / "SOUL.md"


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


@lru_cache(maxsize=1)
def load_soul() -> str:
    """Return ``doc/SOUL.md`` — identity, voice, and behavior (single source of truth).

    Strips the developer-only *Wiring* section so agents see personality rules only.
    """
    if not _SOUL_PATH.exists():
        raise FileNotFoundError(f"Soul file not found at {_SOUL_PATH}")
    text = _SOUL_PATH.read_text(encoding="utf-8")
    marker = "## 4. Wiring"
    if marker in text:
        text = text.split(marker, maxsplit=1)[0].rstrip()
    return text
