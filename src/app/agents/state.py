from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    MAX_STEPS = "max_steps"
    ERROR = "error"


@dataclass
class AgentState:
    """Observable state for one agent execution."""

    goal: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    observations: list[Any] = field(default_factory=list)
    status: AgentStatus = AgentStatus.PENDING
    final_result: Any | None = None
