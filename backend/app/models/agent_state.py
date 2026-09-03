from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field


class AgentStateSnapshot(Document):
    """
    LangGraph state snapshots for debugging and resumability.
    MongoDB's flexible schema handles varying state shapes per agent.
    """

    session_id: Indexed(str)
    agent_type: str  # growth, buyer, guardian, catalog
    merchant_id: Optional[str] = None
    state_data: dict  # Flexible LangGraph state
    checkpoint_type: str  # start, step, end, error
    step_number: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "agent_state_snapshots"
        indexes = [
            "session_id",
            "agent_type",
            "checkpoint_type",
            [("session_id", 1), ("step_number", 1)],
        ]
