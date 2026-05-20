"""Safety Guard for Lucy Runtime.

Provides token budget management, tool call loop detection,
and command execution permission tiers.
"""

import time
from collections import defaultdict


class ToolCallLoopDetector:
    """Detects when the same tool+params fires repeatedly (Mercury-inspired)."""

    def __init__(self, max_repeats: int = 3):
        self.max_repeats = max_repeats
        self._history: list[str] = []

    def check(self, tool_name: str, params_hash: str) -> bool:
        """Returns True if safe to proceed, False if loop detected."""
        key = f"{tool_name}:{params_hash}"
        self._history.append(key)

        # Check last N entries for same key
        recent = self._history[-self.max_repeats:]
        if len(recent) == self.max_repeats and all(k == key for k in recent):
            return False
        return True

    def reset(self):
        self._history.clear()


class TokenBudget:
    """Daily token budget with auto-concise at threshold (Mercury-inspired)."""

    def __init__(self, daily_limit: int = 500_000, concise_threshold: float = 0.7):
        self.daily_limit = daily_limit
        self.concise_threshold = concise_threshold
        self._usage: dict[str, int] = defaultdict(int)  # date_str -> tokens

    def _today(self) -> str:
        return time.strftime("%Y-%m-%d")

    @property
    def used_today(self) -> int:
        return self._usage[self._today()]

    @property
    def remaining(self) -> int:
        return max(0, self.daily_limit - self.used_today)

    @property
    def should_concise(self) -> bool:
        return self.used_today >= self.daily_limit * self.concise_threshold

    @property
    def is_exhausted(self) -> bool:
        return self.used_today >= self.daily_limit

    def record(self, tokens: int):
        self._usage[self._today()] += tokens

    def get_concise_instruction(self) -> str | None:
        if self.is_exhausted:
            return None  # Should not proceed
        if self.should_concise:
            return "Keep your response concise and brief to conserve today's remaining token budget."
        return None


# Command permission tiers (Mercury-inspired)
BLOCKED_COMMANDS = frozenset([
    "rm -rf /", "rm -rf /*", "sudo rm", "mkfs", "dd if=",
    ":(){ :|:& };:", "chmod -R 777 /", "shutdown", "reboot",
    "passwd", "userdel", "useradd", "visudo",
    "> /dev/sda", "mv /* /dev/null",
])

AUTO_APPROVED_COMMANDS = frozenset([
    "ls", "cat", "head", "tail", "grep", "find", "wc",
    "git status", "git log", "git diff", "git branch",
    "pwd", "whoami", "date", "echo", "which", "type",
    "python --version", "node --version", "pip list",
])

BLOCKED_PATTERNS = [
    "sudo ", "rm -rf", "> /dev/", "| sudo",
    "curl | sh", "curl | bash", "wget | sh",
]


def classify_command(command: str) -> str:
    """Classify a shell command into permission tiers.

    Returns: 'blocked', 'auto', or 'review'
    """
    cmd_stripped = command.strip().lower()

    # Check blocked list
    if cmd_stripped in BLOCKED_COMMANDS:
        return "blocked"

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in cmd_stripped:
            return "blocked"

    # Check auto-approved
    cmd_base = cmd_stripped.split()[0] if cmd_stripped else ""
    for approved in AUTO_APPROVED_COMMANDS:
        if cmd_stripped == approved or cmd_stripped.startswith(approved + " "):
            return "auto"

    # Check if it's a safe read-only command
    if cmd_base in {"ls", "cat", "head", "tail", "grep", "find", "wc", "pwd", "whoami", "date", "echo", "which", "type", "env", "printenv"}:
        return "auto"

    return "review"


class SafetyGuard:
    """Combined safety guard for Lucy Runtime."""

    def __init__(self, daily_token_limit: int = 500_000, max_tool_calls_per_turn: int = 15):
        self.loop_detector = ToolCallLoopDetector()
        self.token_budget = TokenBudget(daily_limit=daily_token_limit)
        self.max_tool_calls_per_turn = max_tool_calls_per_turn
        self._tool_calls_this_turn = 0

    def start_turn(self):
        """Reset per-turn counters."""
        self._tool_calls_this_turn = 0
        self.loop_detector.reset()

    def can_call_tool(self, tool_name: str, params_hash: str = "") -> tuple[bool, str]:
        """Check if a tool call is allowed.

        Returns (allowed, reason).
        """
        if self.token_budget.is_exhausted:
            return False, "Daily token budget exhausted"

        self._tool_calls_this_turn += 1
        if self._tool_calls_this_turn > self.max_tool_calls_per_turn:
            return False, f"Tool call limit ({self.max_tool_calls_per_turn}) reached this turn"

        if not self.loop_detector.check(tool_name, params_hash):
            return False, f"Loop detected: {tool_name} called {self.loop_detector.max_repeats}+ times with same params"

        return True, "ok"

    def check_command(self, command: str) -> tuple[bool, str]:
        """Check if a shell command is allowed.

        Returns (allowed, reason).
        """
        tier = classify_command(command)
        if tier == "blocked":
            return False, f"Command blocked by safety policy: {command}"
        return True, tier  # "auto" or "review"

    def record_tokens(self, tokens: int):
        self.token_budget.record(tokens)
