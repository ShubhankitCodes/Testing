"""
spine.py — the end-to-end pipeline skeleton (Week 1).

Runs one conversation through every stage in order:

    audio-in -> transcribe -> controller -> retrieve -> model -> speak

Every stage except the controller is a stub for Week 1: it logs the
event(s) the frozen schema (eventlog/schema.md) says it should, and hands a
hardcoded value to the next stage. The controller is not a stub — it calls
the real decide() from controller/decide.py, which currently always answers
"noop" (see that module's docstring for why that's the right answer this
week).

The point, per pipeline/README.md, isn't intelligence. It's that a
conversation flows all the way through, every step gets logged in the
frozen format, and each stage is a clearly separated function so a
teammate's real component can drop in and replace one stub at a time
without touching this file's overall shape.
"""

import sys
import time
from pathlib import Path

# controller/ and eventlog/ are sibling top-level folders, not subpackages
# of pipeline/. Running this file directly (`python3 pipeline/spine.py`)
# only puts pipeline/'s own directory on sys.path, so without this, the
# imports below fail with ModuleNotFoundError. Adding the repo root once,
# here, means both `python3 pipeline/spine.py` and `python3 -m
# pipeline.spine` work the same way.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from controller.decide import decide
from eventlog.log_writer import LogWriter


def _sleep_ms(ms: float) -> None:
    """
    Sleep for roughly `ms` milliseconds.

    Purely cosmetic: with every stage a stub, all six events would
    otherwise land at nearly the same t_ms and the log would read like
    everything happened at once. A small pause between stages spreads the
    timestamps out so a replay through the harness's timeline viewer
    looks like a real conversation's pacing, not an instant burst.
    """
    time.sleep(ms / 1000)


# ---------------------------------------------------------------------------
# Stage 1 — audio-in
# ---------------------------------------------------------------------------
def audio_in() -> str:
    """
    Real version: a live microphone stream. For Week 1, a hardcoded
    utterance stands in for "the user just said this."
    """
    return "what time does the pool close"


# ---------------------------------------------------------------------------
# Stage 2 — transcribe
# ---------------------------------------------------------------------------
def transcribe(utterance: str, log_writer: LogWriter, turn_id: int) -> str:
    """
    Real version: faster-whisper streaming speech-to-text, emitting a
    partial guess every 300-500ms as audio arrives, then a final
    transcription once the user stops (see audio/README.md).

    The stub fakes that shape with a single partial (a leading fragment of
    the sentence, as if the tail end hasn't been heard yet), then the full
    text as the final, then user_end once the user is judged to have
    stopped talking.
    """
    partial_text = utterance.rsplit(" ", 2)[0]  # e.g. "what time does the"
    log_writer.log_event("user", "asr_partial", {"text": partial_text}, turn_id)
    _sleep_ms(280)  # simulate the rest of the utterance streaming in

    log_writer.log_event("user", "asr_final", {"text": utterance}, turn_id)
    _sleep_ms(10)  # simulate the brief silence needed to confirm the user stopped

    log_writer.log_event("user", "user_end", {}, turn_id)
    return utterance


# ---------------------------------------------------------------------------
# Stage 3 — controller
# ---------------------------------------------------------------------------
def controller_decide(transcript: str, log_writer: LogWriter, turn_id: int) -> dict:
    """
    Not a stub. Calls the real decide() from controller/decide.py, which
    logs its own controller_action event internally. The pipeline calls it
    exactly the way it always will, so swapping in the real value-vs-delay
    decision logic later requires no change here — only decide()'s body
    changes.
    """
    # "belief" is whatever situation snapshot the real controller will
    # eventually reason over. decide() ignores it in Week 1; it's passed
    # here so the call shape already matches what it will be later.
    belief = {"transcript": transcript}
    _sleep_ms(15)  # simulate the moment it takes to assemble a belief and decide
    return decide(belief, log_writer=log_writer, turn_id=turn_id)


# ---------------------------------------------------------------------------
# Stage 4 — retrieve
# ---------------------------------------------------------------------------
def retrieve(query: str, log_writer: LogWriter, turn_id: int) -> list:
    """
    Real version: embed the query and search the FAISS index built from
    retrieval/corpus/, returning the top-k passages (see
    retrieval/README.md). The stub logs a search launching, waits like a
    real index lookup would take, then "returns" two hardcoded passages.
    """
    log_writer.log_event("system", "retrieval_launched", {"query": query}, turn_id)
    _sleep_ms(120)  # simulate embedding the query + a FAISS lookup

    passages = [
        "Pool hours: the pool is open daily from 6:00 AM to 10:00 PM.",
        "The pool deck closes 30 minutes before the pool itself for cleaning.",
    ]
    scores = [0.91, 0.78]
    log_writer.log_event(
        "system",
        "retrieval_result",
        {"passages": passages, "scores": scores},
        turn_id,
    )
    return passages


# ---------------------------------------------------------------------------
# Stage 5 — model
# ---------------------------------------------------------------------------
def generate_answer(passages: list, log_writer: LogWriter, turn_id: int) -> str:
    """
    Real version: an ~8B instruct model served via vLLM, with per-token
    logprobs exposed alongside the answer (see llm/README.md). The stub
    skips straight to a hardcoded answer, but still logs the two timing
    events the schema expects: the first token appearing, then the full
    answer.
    """
    _sleep_ms(110)  # simulate time-to-first-token
    log_writer.log_event("system", "llm_first_token", {"token": "The"}, turn_id)

    answer = "The pool is open until 10 PM."
    _sleep_ms(160)  # simulate the rest of the answer generating
    log_writer.log_event("system", "llm_final", {"text": answer}, turn_id)
    return answer


# ---------------------------------------------------------------------------
# Stage 6 — speak
# ---------------------------------------------------------------------------
def speak(answer: str, log_writer: LogWriter, turn_id: int) -> None:
    """
    Real version: local TTS (e.g. piper) synthesizing and streaming audio
    out (see audio/README.md). The stub prints the answer as a stand-in
    for "audio played," and logs tts_first_audio — the TTFA anchor the
    harness uses: Time To First Audio is this event's t_ms minus
    user_end's t_ms.
    """
    _sleep_ms(80)  # simulate synthesis time before the first sample plays
    log_writer.log_event("system", "tts_first_audio", {}, turn_id)
    print(f'  system speaks: "{answer}"')


# ---------------------------------------------------------------------------
# The spine itself
# ---------------------------------------------------------------------------
def run_conversation(conversation_id: str) -> Path:
    """
    Runs one full, hardcoded conversation through every stage above, in
    order, logging every event to logs/<conversation_id>.jsonl per
    eventlog/schema.md. Returns the path to that log file.
    """
    log_writer = LogWriter(conversation_id=conversation_id)
    turn_id = 1  # Week 1's canned conversation is a single turn.

    try:
        utterance = audio_in()
        print(f'  user says:      "{utterance}"')

        transcript = transcribe(utterance, log_writer, turn_id)

        action = controller_decide(transcript, log_writer, turn_id)
        print(f"  controller:     {action}")

        passages = retrieve(transcript, log_writer, turn_id)
        print(f"  retrieved:      {len(passages)} passage(s)")

        answer = generate_answer(passages, log_writer, turn_id)
        speak(answer, log_writer, turn_id)
    finally:
        # Always close, even if a stage above raises — otherwise whatever
        # is still sitting in the writer thread's queue never reaches
        # disk, and we'd lose the tail of the conversation.
        log_writer.close()

    return log_writer._path


if __name__ == "__main__":
    print("Running one canned conversation through the spine...\n")
    log_path = run_conversation("conv_001")
    print(f"\nWrote log to: {log_path}")
