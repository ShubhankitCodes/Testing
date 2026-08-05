# logging/ — Event Log (the shared contract)

**This is the most important folder in the repo. Read it before writing any code that 
produces or reads logs.**

## What this folder is

Every conversation the system runs produces one log file: a timestamped record of every 
single thing that happened (words heard, searches launched, decisions made, audio spoken). 
Every number and figure in our final paper is computed from these logs.

Because six people's code all writes to this same log, the format must be agreed and 
frozen. That agreement is the schema in `schema.md`. Once frozen, nobody changes it without 
telling the whole team.

## Why it matters

Live audio bugs cannot be reproduced — a timing glitch happens once and is gone. The log 
is our time machine: we replay any conversation from its log to see exactly what happened. 
It is also how the harness computes metrics and how experiments are scored. Logging is not 
overhead; it is the core deliverable of Week 1.

## The format: JSONL

The log is a `.jsonl` file — one JSON object per line, one line per event. Every line has 
the same core fields:

| Field | Meaning |
|-------|---------|
| `t_ms` | Timestamp in milliseconds from a single monotonic clock (see rule below) |
| `conversation_id` | Which conversation this belongs to |
| `turn_id` | Which turn within the conversation |
| `actor` | `"user"` or `"system"` |
| `event_type` | What kind of event (see list below) |
| `payload` | An object with details specific to that event type |

## Event types (Week 1 set)

| `event_type` | When it fires | Key payload fields |
|--------------|---------------|--------------------|
| `asr_partial` | A live, revisable transcription guess | `text` |
| `asr_final` | The finalized transcription of a user turn | `text` |
| `user_end` | The user is judged to have stopped speaking | (none) |
| `retrieval_launched` | A document search starts | `query` |
| `retrieval_result` | Search returns passages | `passages`, `scores` |
| `controller_action` | The controller makes a decision | `action` (e.g. `retrieve`, `wait`, `speak`, `noop`) |
| `llm_first_token` | The model produces its first output token | `token` |
| `llm_final` | The model's full answer is ready | `text` |
| `tts_first_audio` | The first sound of the reply goes out | (none) — **this is the TTFA anchor** |
| `barge_in` | The user interrupts while the system is speaking | (none) |

More event types will be added in later weeks. Add them here first, then in code.

## The one hard rule

**Use one monotonic clock for `t_ms` everywhere.** A monotonic clock only ever moves 
forward and is not affected by the system clock changing. In Python: 
`time.monotonic_ns() // 1_000_000`. If different components use different clocks, the 
timeline is meaningless and the whole month's data is unreliable.

**Second rule:** never write to the log from the audio thread directly (it would stutter 
the audio). Queue log events to a separate writer. A helper for this lives in this folder.

## Example log line

```json
{"t_ms": 10432, "conversation_id": "conv_001", "turn_id": 3, "actor": "user", "event_type": "asr_final", "payload": {"text": "what time does the pool close"}}
```

## Week 1 goal for this folder

- `schema.md` written and frozen (owner: Renya, Day 1).
- A small `log_writer.py` helper that any component can import to append events in this 
  exact format, using the shared monotonic clock.

## Status

Schema: **to be frozen Day 1.** Until it is frozen, do not write log-producing or 
log-reading code.
