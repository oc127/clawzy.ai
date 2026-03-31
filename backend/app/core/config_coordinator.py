"""Config Coordinator — serializes all OpenClaw configuration writes.

Routes every modification to openclaw.json, auth-profiles.json, and
docker-compose.yml through a single asyncio Lock to prevent concurrent
deployment processes from overwriting each other's changes.

Also implements three-way merge so critical gateway config keys are never
silently lost when an external process modifies a file between our read
and write.
"""

import asyncio
import copy
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Single process-wide lock — all config writes must acquire this.
_write_lock = asyncio.Lock()

# Key paths in openclaw.json that must NEVER be overwritten by a merge.
# Each entry is a tuple of nested dict keys (path from root).
_PROTECTED_OPENCLAW_KEYS: list[tuple[str, ...]] = [
    ("gateway", "http", "endpoints", "chatCompletions", "enabled"),
    ("gateway", "bind"),
]


# ── Low-level helpers ────────────────────────────────────────────────────────

def _file_hash(path: Path) -> str:
    """Return SHA-256 hex digest of *path*, or '' if the file does not exist."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return ""


def _deep_get(obj: Any, keys: tuple[str, ...]) -> Any:
    """Traverse a nested dict by key-path; return None if any level is missing."""
    for k in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(k)
        if obj is None:
            return None
    return obj


def _deep_set(obj: dict, keys: tuple[str, ...], value: Any) -> None:
    """Set *value* at a nested key-path, creating intermediate dicts as needed."""
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    obj[keys[-1]] = value


# ── Three-way merge ──────────────────────────────────────────────────────────

def _three_way_merge(base: dict, ours: dict, theirs: dict) -> dict:
    """Merge *theirs* onto *ours* where *theirs* diverged from *base*.

    Conflict resolution:
    - Key changed only by theirs  → accept theirs
    - Key changed only by ours    → keep ours
    - Key changed by both         → ours wins
    - Key new in theirs, not ours → accept theirs
    - Key deleted by ours         → stays deleted

    After merging, all protected key-paths are forcibly restored from *ours*
    so critical gateway settings can never be silently removed.
    """
    merged = copy.deepcopy(ours)

    def _merge_recursive(b: dict, o: dict, t: dict, m: dict) -> None:
        for key, t_val in t.items():
            if key not in b:
                # New key added only by theirs — accept if ours didn't add it
                if key not in o:
                    m[key] = t_val
            elif key not in o:
                # Deleted by ours — respect the deletion
                pass
            elif isinstance(t_val, dict) and isinstance(o.get(key), dict):
                _merge_recursive(
                    b.get(key, {}),
                    o[key],
                    t_val,
                    m.setdefault(key, copy.deepcopy(o[key])),
                )
            elif t_val != b[key] and o[key] == b[key]:
                # Only theirs changed from base — accept
                m[key] = t_val
            # else: ours changed (ours wins) or both changed (ours wins)

    _merge_recursive(base, ours, theirs, merged)

    # Re-apply protected keys from ours — they must survive any merge
    for key_path in _PROTECTED_OPENCLAW_KEYS:
        our_val = _deep_get(ours, key_path)
        if our_val is not None:
            _deep_set(merged, key_path, our_val)

    return merged


# ── Public API ───────────────────────────────────────────────────────────────

async def atomic_update_json(
    path: Path,
    mutate: Callable[[dict], dict],
) -> dict:
    """Atomically read, mutate, and write a JSON config file.

    Steps (all under the global lock):
    1. Read current file → *base*
    2. Apply *mutate(base)* → *ours*
    3. Re-read file and compare hash; if changed by an external process → *theirs*
    4. Three-way-merge(base, ours, theirs) to reconcile
    5. Write result atomically via a .tmp side-file

    Returns the final dict that was written.
    """
    async with _write_lock:
        # --- Step 1: read base state ---
        base_hash = _file_hash(path)
        try:
            base: dict = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (json.JSONDecodeError, OSError):
            base = {}

        # --- Step 2: apply mutation ---
        ours = mutate(copy.deepcopy(base))

        # --- Step 3: detect external modification ---
        current_hash = _file_hash(path)
        if current_hash != base_hash:
            try:
                theirs: dict = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError, FileNotFoundError):
                theirs = {}

            logger.warning(
                "[config_coordinator] %s changed externally during update; "
                "performing three-way merge",
                path,
            )
            ours = _three_way_merge(base, ours, theirs)

        # --- Step 4: atomic write via .tmp ---
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(ours, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(path)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise

        logger.debug("[config_coordinator] wrote %s", path)
        return ours


async def read_json(path: Path) -> dict:
    """Read a JSON config file under the global lock (consistent snapshot)."""
    async with _write_lock:
        try:
            return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (json.JSONDecodeError, OSError):
            return {}
