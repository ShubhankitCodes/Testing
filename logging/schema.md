# Event Log Schema (FROZEN v1)

Do not change without notifying the whole team.

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
