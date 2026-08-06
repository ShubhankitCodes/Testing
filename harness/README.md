# harness/ — Metrics & Replay Tools

**Owner: Shubhankit**  
This README covers Week 1. More metrics and analysis tools will be added here as we go.

## What this folder is

The scoreboard and the debugging viewer. Two things: a tool that reads an event log and 
computes metrics (starting with the main timing metric), and a viewer that turns a raw log 
into a readable timeline of what happened and when.

## Why it matters

The replay viewer becomes the whole team's debugging tool for the entire month. Every time 
someone asks "why did this conversation go wrong?", the answer comes from your timeline 
viewer. This folder builds against the frozen log schema (`eventlog/schema.md`), not the 
live pipeline, so you are fully unblockable from Day 1 — you do not have to wait for anyone.

## Week 1 goal (your deliverable)

1. A log-reader that computes TTFA (Time To First Audio) from a log file.
2. A replay-to-timeline viewer that prints a readable sequence of events from a log.
3. Basic statistics helpers (percentiles, a confidence-interval function) for later use.

## Background you need first

Read `eventlog/schema.md`. That is the exact format of the log files you will read. Every 
line is one JSON object with fields `t_ms`, `conversation_id`, `turn_id`, `actor`, 
`event_type`, and `payload`. Your tools parse these lines.

**TTFA (Time To First Audio)** is the key metric: the gap in milliseconds between the user 
finishing speaking and the first sound of the reply going out. In log terms, it is the 
`t_ms` of the `tts_first_audio` event minus the `t_ms` of the `user_end` event, within the 
same turn.

## How to start (step by step)

### Step 1 — Make a fake log to test against

You do not need the real pipeline. Hand-write a small `.jsonl` file with a few events 
(a `user_end`, then a `tts_first_audio` a few hundred ms later, etc.) following the schema. 
This is your test input.

### Step 2 — Log reader + TTFA (`metrics.py`)

Write a script that:
1. Opens a `.jsonl` log file and reads it line by line, parsing each as JSON.
2. Groups events by `turn_id`.
3. For each turn, finds the `user_end` and `tts_first_audio` events and computes TTFA.
4. Prints a summary (per-turn TTFA, and the average / p95 across turns).

Run it on your fake log and confirm the numbers are right.

### Step 3 — Timeline viewer (`replay.py`)

Write a tool that reads a log and prints a clean, ordered, human-readable timeline, e.g.:

[  0 ms] user      asr_partial     "what time does the"
[420 ms] user      asr_final       "what time does the pool close"
[430 ms] user      user_end
[440 ms] system    controller_action  retrieve
[560 ms] system    retrieval_result   (3 passages)
[900 ms] system    tts_first_audio     -> TTFA = 470 ms

This is the tool everyone will use to understand what happened in a conversation. Make it 
clear and pleasant to read.

### Step 4 — Statistics helpers (`stats.py`)

Add simple helpers for later experiments: a percentile function (for p95) and a bootstrap 
confidence-interval function (repeatedly resample a list of numbers to estimate a range). 
You will not use these heavily in Week 1, but having them ready helps later.

## Not in Week 1 (do not start these yet)

- Running actual experiments (that is Weeks 3–4).
- Comparing policies over logs (re-simulation) — later.

## Definition of done (Week 1)

Feed your tools a sample log and they (a) compute TTFA correctly and (b) draw a clean, 
readable timeline. The statistics helpers exist and are tested on toy inputs.

## Coordinate with

Nobody directly for Week 1 — you build against the schema, which is frozen. Just make sure 
you are reading the latest `eventlog/schema.md` if it ever updates.
