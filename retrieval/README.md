# retrieval/ — Retrieval & Corpus

**Owner: Lakshya**  
This README covers Week 1. Later phases (query rewriting, public benchmark datasets) will 
be added here as we go.

## What this folder is

This is the knowledge the assistant answers from. It has two parts: a collection of hotel 
documents (the `corpus/` subfolder), and the search system that, given a question, returns 
the most relevant passages from those documents.

## Why it matters

The whole system answers questions using what this folder retrieves. If retrieval returns 
the wrong passage, the answer is wrong no matter how good everything else is. This folder 
has no dependencies on anyone else's code, so you can start at full speed on Day 1.

## Week 1 goal (your deliverable)

1. About 60 short hotel documents written and saved in `corpus/`.
2. A search index built over them.
3. A `search(query, k)` function that returns the k most relevant passages.
4. A short recall report proving the right passages come back.

## How to start (step by step)

### Step 1 — Write the documents (do this first; it is the biggest time sink)

Write ~60 short documents (a paragraph or a few each) covering realistic hotel information:

- Pool, gym, and spa hours
- Check-in and check-out times, late-checkout policy
- Restaurant and room-service menus (veg and non-veg), breakfast timings
- Cancellation policy, pet policy, parking, wifi
- Amenities, nearby attractions, airport shuttle

Save them as plain `.txt` or `.md` files in `corpus/`, one topic per file.

**Important:** deliberately plant a few contradictions (e.g. one doc says the pool closes 
at 10 PM, another says 9 PM). Keep a note of which documents contradict — a later 
experiment tests whether the system notices conflicts.

### Step 2 — Set up your tools

You will use two Python libraries: `sentence-transformers` (to turn text into vectors) and 
`faiss-cpu` (the search index). Add them to the shared `requirements.txt` (ask the integration lead if it 
does not exist yet) rather than installing them only on your machine.

### Step 3 — Build the index (`build_index.py`)

Write a script that:
1. Reads all files from `corpus/`.
2. Splits each into chunks (a paragraph, or ~100–300 words; at this scale you can even 
   treat each short doc as one chunk to start).
3. Loads a small embedding model (e.g. `BAAI/bge-small-en`).
4. Turns every chunk into a vector.
5. Builds a FAISS **flat** index (flat = exact search, which is the correct choice under 
   ~100k items — you have ~60) and adds all the vectors.
6. Saves the index to disk plus a mapping from each vector back to its original chunk text.

### Step 4 — Write the search function (`search.py`)

A function `search(query, k=5)` that:
1. Embeds the incoming question with the **same** model used in Step 3. (Critical: same 
   model, or the vectors are not comparable.)
2. Asks FAISS for the k nearest chunk-vectors.
3. Looks up their original text via the mapping.
4. Returns those k passages.

Keep its input and output simple and documented — Renya will plug this into the pipeline in 
place of the retrieval stub.

### Step 5 — Recall report (`recall_report.md`)

Write 10–15 questions you know the answers to (from your own docs), run `search()` on each, 
and record whether the correct passage came back near the top. A simple table of 
question / top passages / correct? is perfect. This is your proof it works.

## Not in Week 1 (do not start these yet)

- Query rewriting (turning context-dependent questions into standalone ones) — Week 2.
- Public benchmark datasets (SpokenWOZ, Spoken-SQuAD) — Week 2. Background task this week: 
  just confirm they are accessible and research-licensed, and note it. Do not integrate.
- Reranking, hybrid search, chunk-size tuning — later.

## Definition of done (Week 1)

Index built over ~60 docs (with a few planted contradictions), a working `search()` 
function ready to plug in, and a recall report showing sensible passages come back.

## Coordinate with

Whoever builds the scenarios (currently also Lakshya, as a Week-2 task) — the scenario 
answer keys must match what these documents actually say.
