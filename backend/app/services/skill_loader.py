"""Disk-based built-in skill library loader.

Scans backend/skills/<category>/<skill-name>/SKILL.md files, parses YAML
frontmatter, and exposes compact listing + on-demand full-content loading.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# backend/app/services/ → ../../../skills = backend/skills/
_SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass
class BuiltinSkillMeta:
    """Lightweight skill descriptor — loaded on startup."""
    name: str
    description: str
    category: str
    tags: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    platform: str = "all"
    path: Path = field(default_factory=Path)


@dataclass
class BuiltinSkill(BuiltinSkillMeta):
    """Full skill including the SKILL.md body (loaded on demand)."""
    content: str = ""


# ── YAML frontmatter parsing (no external dep) ─────────────────────────────

def _parse_yaml_value(val: str) -> str | list[str]:
    """Parse a simple scalar or inline list from a YAML value string."""
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        return [item.strip().strip('"\'') for item in inner.split(",") if item.strip()]
    return val.strip('"\'')


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text) from a SKILL.md string."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip()] = _parse_yaml_value(val)

    body = text[m.end():]
    return fm, body


# ── Scanning ───────────────────────────────────────────────────────────────

def _scan_skills_dir() -> list[BuiltinSkillMeta]:
    """Walk skills/ and return compact metadata list."""
    if not _SKILLS_DIR.exists():
        logger.warning("Built-in skills directory not found: %s", _SKILLS_DIR)
        return []

    skills: list[BuiltinSkillMeta] = []
    for skill_file in sorted(_SKILLS_DIR.rglob("SKILL.md")):
        try:
            text = skill_file.read_text(encoding="utf-8")
            fm, _ = _parse_frontmatter(text)

            name = fm.get("name", skill_file.parent.name)
            description = fm.get("description", "")
            category = fm.get("category", skill_file.parent.parent.name)
            tags = fm.get("tags", [])
            triggers = fm.get("triggers", [])
            version = fm.get("version", "1.0.0")
            platform = fm.get("platform", "all")

            if isinstance(tags, str):
                tags = [tags]
            if isinstance(triggers, str):
                triggers = [triggers]

            skills.append(BuiltinSkillMeta(
                name=name,
                description=description,
                category=category,
                tags=tags,
                triggers=triggers,
                version=version,
                platform=platform,
                path=skill_file,
            ))
        except Exception as exc:
            logger.warning("Failed to parse skill file %s: %s", skill_file, exc)

    logger.info("Loaded %d built-in skill definitions", len(skills))
    return skills


# ── Public API ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def list_all_skills() -> list[BuiltinSkillMeta]:
    """Return compact metadata for all built-in skills (cached after first call)."""
    return _scan_skills_dir()


def reload_skills() -> list[BuiltinSkillMeta]:
    """Force re-scan of disk (clears the lru_cache)."""
    list_all_skills.cache_clear()
    return list_all_skills()


def get_skill(name: str) -> BuiltinSkill | None:
    """Load full SKILL.md content for a single skill by name."""
    for meta in list_all_skills():
        if meta.name == name:
            try:
                text = meta.path.read_text(encoding="utf-8")
                _, body = _parse_frontmatter(text)
                return BuiltinSkill(**meta.__dict__, content=body.strip())
            except Exception as exc:
                logger.error("Failed to read skill content for '%s': %s", name, exc)
                return None
    return None


def search_skills(query: str) -> list[BuiltinSkillMeta]:
    """Search skills by name, description, tags, or triggers (case-insensitive)."""
    q = query.lower()
    results = []
    for skill in list_all_skills():
        searchable = " ".join([
            skill.name,
            skill.description,
            skill.category,
            " ".join(skill.tags),
            " ".join(skill.triggers),
        ]).lower()
        if q in searchable:
            results.append(skill)
    return results


def match_skills(user_message: str, max_results: int = 3) -> list[BuiltinSkillMeta]:
    """Match built-in skills by trigger keyword hits in the user message.

    Scores each skill by the number of its trigger keywords that appear in the
    message.  Returns up to max_results skills ranked by score.
    """
    msg_lower = user_message.lower()
    scored: list[tuple[int, BuiltinSkillMeta]] = []

    for skill in list_all_skills():
        if not skill.triggers:
            continue
        hits = sum(1 for t in skill.triggers if t.lower() in msg_lower)
        if hits > 0:
            scored.append((hits, skill))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:max_results]]


def build_skills_index_prompt() -> str:
    """Return a compact skills directory for inclusion in a system prompt.

    Token budget: ~80 tokens per skill × 35 skills ≈ 2800 tokens max.
    Only name + description + category + top-3 triggers per skill.
    """
    skills = list_all_skills()
    if not skills:
        return ""

    lines = ["## Available Built-in Skills\n"]
    by_category: dict[str, list[BuiltinSkillMeta]] = {}
    for s in skills:
        by_category.setdefault(s.category, []).append(s)

    for category, cat_skills in sorted(by_category.items()):
        lines.append(f"### {category}")
        for s in cat_skills:
            trigger_hint = ", ".join(s.triggers[:3])
            lines.append(f"- **{s.name}**: {s.description} _(triggers: {trigger_hint})_")
        lines.append("")

    lines.append(
        "_Invoke a skill by asking about its triggers. "
        "Full instructions will be loaded automatically._\n"
    )
    return "\n".join(lines)
