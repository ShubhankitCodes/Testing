# pipeline/ — The Spine (end-to-end integration)

**Owner: integration lead**  
This README covers Week 1.

## What this folder is

The spine that connects every stage into one working loop: audio in → transcribe → retrieve 
→ model → speak → audio out. In Week 1 every stage is a stub that returns a hardcoded value 
and logs that it ran. The point is not intelligence; it is that a conversation flows all the 
way through and every step is logged.

## Why it matters

This is the centre everyone else plugs into. Until the spine exists, nobody can integrate 
their real component. It is also the reference example of the log format that every other 
component copies. The classic project failure is polishing components separately and 
integrating at the end; the spine exists to prevent that by making integration continuous.

## Week 1 goal (your deliverable)

1. An end-to-end pipeline where each stage is a stub, connected in order.
2. A canned conversation runs start to finish: fake audio in, hardcoded answer spoken out.
3. Every stage writes to the log in the frozen schema.
4. As real components become ready, their stubs are swapped out and the log still reads 
   correctly.

## How to start (step by step)

### Step 1 — Freeze the schema first

Before anything, make sure `logging/schema.md` is frozen and the shared `log_writer` helper 
exists. Nothing in the pipeline should be built before the schema is set, since every stage 
logs against it.

### Step 2 — Build each stage as a stub

Create a simple stage for each step of the loop. Each stub does three things: log that it 
ran (in the frozen schema), pass a hardcoded value to the next stage, and return. Stages:
- audio-in (start with a canned audio file or a fixed transcript)
- transcribe → logs `asr_final` with fixed text
- controller → logs `controller_action` with `noop`
- retrieve → logs `retrieval_launched` / `retrieval_result` with fixed passages
- model → logs `llm_final` with a hardcoded answer
- speak → logs `tts_first_audio` and "plays" a fixed sentence

### Step 3 — Connect them into one loop

Wire the stages in order so one call runs the whole chain and produces a complete log for 
one conversation. Confirm the log can be read by the harness's timeline viewer.

### Step 4 — Swap stubs for real components

As each teammate's real component becomes ready (audio, retrieval, model), replace the 
matching stub with the real thing and confirm the pipeline still runs and the log still 
parses. This is the integration work that runs through the rest of Week 1 and beyond.

## Definition of done (Week 1)

One full conversation runs end to end from a clean checkout of the repo, every stage logged, 
and the log replays correctly on the harness timeline viewer.

## Coordinate with

Everyone — this is where all components come together. Audio, retrieval, and model each get 
swapped into the spine here as they become ready.
