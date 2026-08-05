# simulator/ — Fake-User Scenarios

**Owner: Lakshya (second priority, after the retrieval corpus)**

## What this folder is

The fake user: software that generates test conversations (guest goals, the questions they 
would ask) with a known correct answer for each. This lets us run many test conversations 
without needing live people every time.

## Status: not a Week 1 deliverable

The full simulator is needed for later experiments (Weeks 3–4), not Week 1. The detailed 
brief will be added here in Week 2.

For Week 1, focus is on the retrieval corpus (see `retrieval/README.md`). If there is spare 
time, a light head start is fine: draft a scenario format (a guest goal, the question, the 
expected answer, and whether a document lookup is needed) and a handful of example 
scenarios.

## Important when this starts

The answer key for each scenario must match what the hotel documents in `retrieval/corpus/` 
actually say. Because the same person owns both the corpus and the scenarios, this stays 
consistent.
