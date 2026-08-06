# Pre-Registration — Voice-RAG Controller Experiments

This document records what each experiment measures and what counts as success or failure, 
decided BEFORE running them. We do not change success criteria after seeing results. 
Owner: Yashmitha. Sign-off: Ryan.

Status: DRAFT — criteria to be confirmed with the team.

## Guiding principle
The project claims three live decisions (when to retrieve, what to remember, when to speak) 
are better made by one unified controller than three separate rules. Each experiment below 
tests one assumption behind that claim. All outcomes, including failures, will be reported.

## Experiment 1 — Signal validity (the gatekeeper)
- Question: When the language model is uncertain (measured from its confidence numbers / 
  logprobs), does that reliably indicate it needs to retrieve a document?
- How: Offline, over questions with known answers and known "was retrieval needed" labels. 
  Score each candidate signal with AUC (0.5 = useless, 1.0 = perfect).
- Success: best signal AUC >= 0.7.
- Kill criterion: best signal AUC < 0.6 -> pivot away from uncertainty-triggered retrieval 
  to a backup approach (draft an answer, verify it, retrieve only if verification fails).
- Runs first; gates the rest.

## Experiment 2 — Timing value
- Question: Does timing retrievals to happen while the user is still talking hide the delay?
- How: Fix the trigger and retrieval budget; vary only WHEN retrieval fires — reactive vs 
  at sentence boundaries vs during predicted user-still-talking windows. Compare TTFA (time 
  to first audio) at matched answer accuracy. 5 seeds, paired bootstrap for intervals.
- Success: forecast-timed retrieval gives lower p95 TTFA at equal accuracy.
- Failure: no timing benefit -> "timing is decoration"; contribution shrinks to trigger 
  quality.

## Experiment 3 — Coupling value (the headline)
- Question: Does one unified controller beat well-tuned separate controllers?
- How: Compare our unified controller against two rivals we build and tune equally: 
  (A) three independent best controllers sharing nothing; (B) the same three given a shared 
  latency/compute price but no shared state. Compare as accuracy-vs-latency curves across a 
  grid of settings. 5 seeds.
- Success (pre-committed): our curve clearly beats rival B over a meaningful region, with 
  non-overlapping confidence bands, in at least 3 of 5 seeds. Ties are reported as ties.
- Three honest outcomes, all publishable: unified wins (thesis confirmed); rival B ties 
  ("shared prices suffice, full unification unnecessary"); nothing beats simple heuristics 
  ("coupling intuition was wrong") + we publish the benchmark.

## Experiment 4 — Memory scheduling (CUT for this deadline)
- Deferring memory operations to idle windows, tested for latency benefit at equal recall. 
  Cut from scope for the current deadline (per our Risk-4 scope rule). Memory still runs 
  (simple size-triggered) but we make no scheduling claims.

## Quality bars (never cut, apply to all experiments)
- 5 seeds per reported result.
- Every baseline gets the same tuning effort as our method.
- Success criteria frozen before data exists.
- TTFA measured at the audio boundary only.
- Every figure regenerable from raw logs by one command.
