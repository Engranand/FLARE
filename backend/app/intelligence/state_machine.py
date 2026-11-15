"""Typed execution state machine for FLARE Milestone 10.2 Intelligence Engine.

Manages query execution lifecycle with strict transition graph enforcement:
- Explicit transition validation preventing skipped steps
- State transition history logging with ISO-8601 timestamps
- Clean separation between active, terminal (ABSTAINED, FAILED), and ready states
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.intelligence.schemas import InvalidStateTransitionError, QueryState


@dataclass(frozen=True)
class StateTransitionRecord:
    """Record of an individual state transition."""
    from_state: QueryState
    to_state: QueryState
    timestamp: datetime
    reason: str | None = None


# Authoritative Directed Graph of Permitted State Transitions
VALID_TRANSITIONS: dict[QueryState, set[QueryState]] = {
    QueryState.RECEIVED: {
        QueryState.NORMALIZED,
        QueryState.FAILED,
    },
    QueryState.NORMALIZED: {
        QueryState.CLASSIFIED,
        QueryState.FAILED,
    },
    QueryState.CLASSIFIED: {
        QueryState.SCOPE_VALIDATED,
        QueryState.FAILED,
    },
    QueryState.SCOPE_VALIDATED: {
        QueryState.PLANNED,
        QueryState.ABSTAINED,
        QueryState.FAILED,
    },
    QueryState.PLANNED: {
        QueryState.READY_FOR_EXECUTION,
        QueryState.FAILED,
    },
    QueryState.READY_FOR_EXECUTION: {
        QueryState.FAILED,
    },
    QueryState.ABSTAINED: set(),  # Terminal state
    QueryState.FAILED: set(),     # Terminal state
}


class ExecutionStateMachine:
    """Deterministic, typed state machine governing query planning and execution."""

    def __init__(self, initial_state: QueryState = QueryState.RECEIVED) -> None:
        self._current_state: QueryState = initial_state
        self._history: list[StateTransitionRecord] = []

    @property
    def current_state(self) -> QueryState:
        """Current state of the query lifecycle."""
        return self._current_state

    @property
    def history(self) -> list[StateTransitionRecord]:
        """Immutable copy of state transition history."""
        return list(self._history)

    def transition_to(self, target_state: QueryState, reason: str | None = None) -> None:
        """Transition the state machine to a new state.
        
        Args:
            target_state: The target QueryState to move into.
            reason: Optional explanation or context for the transition.
            
        Raises:
            InvalidStateTransitionError: If the transition is not permitted by VALID_TRANSITIONS.
        """
        allowed_targets = VALID_TRANSITIONS.get(self._current_state, set())
        if target_state not in allowed_targets:
            raise InvalidStateTransitionError(
                f"Illegal state transition: Cannot move from '{self._current_state.value}' "
                f"to '{target_state.value}'. Allowed transitions from '{self._current_state.value}' "
                f"are: {[s.value for s in allowed_targets]}"
            )

        now = datetime.now(timezone.utc)
        record = StateTransitionRecord(
            from_state=self._current_state,
            to_state=target_state,
            timestamp=now,
            reason=reason,
        )
        self._history.append(record)
        self._current_state = target_state

    def fail(self, error_message: str) -> None:
        """Convenience method to transition directly to FAILED state."""
        self.transition_to(QueryState.FAILED, reason=error_message)
