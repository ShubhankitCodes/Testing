"""
decide.py — the controller's decision function (Week 1 stub).

This is "the decision brain" the top-level README promises: the single place
the pipeline asks, every turn, "what should we do right now?" For Week 1 it
always answers "nothing" — see decide()'s docstring for why that's still a
useful thing to ship.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

# Imported only for type checkers/IDEs, not at runtime. decide() only calls
# log_writer.log_event(...), so it doesn't actually need the LogWriter class
# to exist at import time — this keeps the controller usable even in a
# context where eventlog/ isn't on the path yet (e.g. a standalone test).
if TYPE_CHECKING:
    from eventlog.log_writer import LogWriter


def decide(
    belief: Any,
    log_writer: Optional["LogWriter"] = None,
    turn_id: Optional[int] = None,
) -> dict:
    """
    Decide what the system should do right now.

    This is the stable interface every other component wires against:
    decide(belief) -> action. The signature is deliberately final — only
    the body changes later.

    What "belief" is: whatever situation snapshot the pipeline builds each
    turn (the running transcript, retrieval state, the model's confidence,
    how long the user has been silent, and so on). The Week 1 stub ignores
    it completely; it's accepted here so the pipeline can start calling
    decide() the same way it always will, before belief actually carries
    anything.

    What this returns, for now: always {"action": "noop"} — do nothing.
    That's not a placeholder for its own sake: with every stage in the
    pipeline stubbed out this Week 1, "noop" is the *correct* decision,
    since there's no real retrieval or memory pressure yet to react to.
    Wiring the controller in now, even doing nothing, means every other
    component can log a controller_action turn after turn from day one,
    exactly as it will once the real brain exists.

    What replaces this later: a controller that weighs, for each
    candidate action (retrieve / wait / speak / summarize), the value it
    would add against the delay it costs, and only acts when that's worth
    it. That logic changes; decide(belief) -> action does not, so it's a
    drop-in swap for whatever calls this function.

    Args:
        belief: the current situation snapshot. Unused in Week 1.
        log_writer: if given (together with turn_id), the decision is
            logged as a controller_action event via log_writer.log_event(),
            per eventlog/schema.md.
        turn_id: which turn this decision belongs to. Required alongside
            log_writer for logging to happen.

    Returns:
        A small action dict, e.g. {"action": "noop"}. A dict rather than a
        bare string because later actions carry parameters too (e.g.
        {"action": "retrieve", "query": "..."}) — keeping the shape
        consistent from Week 1 means callers never have to special-case it.
    """
    action = {"action": "noop"}

    # Only log if the caller gave us somewhere to write and a turn to
    # attribute it to — decide() must work standalone (e.g. in tests)
    # without a log_writer.
    if log_writer is not None and turn_id is not None:
        log_writer.log_event(
            actor="system",
            event_type="controller_action",
            payload=action,
            turn_id=turn_id,
        )

    return action


if __name__ == "__main__":
    # A dummy belief — decide() ignores its contents in Week 1, but this
    # is roughly the shape the pipeline will eventually pass in.
    dummy_belief = {
        "transcript_so_far": "what time does the pool close",
        "ms_since_user_stopped": 430,
        "model_confidence": None,
    }

    action = decide(dummy_belief)
    print(f"decide({dummy_belief!r})\n  -> {action}")
