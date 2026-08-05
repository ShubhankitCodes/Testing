# corpus/ — Hotel Documents

**Owner: Lakshya**

## What this folder is

The hotel's documents live here: the knowledge the assistant answers from. About 60 short 
documents covering things like pool and gym hours, check-in and check-out rules, menus, and 
policies.

## How to fill it

See the full instructions in `retrieval/README.md` (Step 1). In short:
- Write ~60 short documents, one topic per file, as `.txt` or `.md`.
- Make them realistic and varied.
- Deliberately plant a few contradictions (e.g. one doc says the pool closes at 10 PM, 
  another says 9 PM) and keep a note of which ones, for a later experiment.

The index-building script reads every file in this folder, so anything you put here becomes 
part of the searchable knowledge.
