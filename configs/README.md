# configs/ — Settings

**Owner: shared**

## What this folder is

Every setting the system uses lives here as a file, never hardcoded inside the code. Model 
names, chunk sizes, the number of passages to retrieve, thresholds, file paths — all of it. 
Keeping settings in one place means anyone can see and change how the system is configured 
without hunting through code, and experiments can be reproduced by pointing at a config.

## Week 1 goal

Create a simple config file (e.g. `config.yaml` or `config.py`) holding the settings used so 
far, for example: the embedding model name, the number of passages to retrieve (k), the 
language model name, and any file paths. As components are built, their settings go here 
rather than being written directly into their code.

## Rule

If you find yourself typing a number or a name directly into code (a model name, a 
threshold, a path), stop and put it in a config file instead. This keeps experiments 
reproducible.
