# llm/ — Setup

How to stand up the model server and verify the confidence numbers are real.

Written provider-agnostic on purpose. The launch command is identical
everywhere; only the environment around it differs. RunPod is our primary,
Azure the fallback. This file is the thing that gets turned into the shared
Dockerfile in Week 2, so keep it accurate — if you run a command that isn't
written here, add it.

---

## What the hardware has to be

An 8B model at bf16 is ~16 GB of weights, plus KV cache and activations.

| VRAM | Verdict |
|------|---------|
| 16 GB | Only fits quantized — **don't**, see below |
| 24 GB (RTX 4090, A10G) | Fits, ~6 GB left for KV cache. Fine for Week 1 |
| 48 GB (A40, L40S, A6000) | Comfortable, and leaves room for the batched simulator runs later |
| 80 GB (A100, H100) | Overkill for 8B — paying for capacity we can't use |

**Do not serve a quantized model for real runs.** The per-token logprobs are
the measurement instrument for Experiment 1. AWQ/GPTQ/FP8 shift the output
distribution, which distorts the exact thing we are measuring, and a reviewer
can fairly ask whether the uncertainty signal survived compression. Serve
`--dtype bfloat16`. That constraint is what sets the 24 GB floor.

---

## Development: no GPU, no cost

`llm.backend: mock` in `configs/config.yaml` is the default, and it's what you
should use for everything except real data collection. The mock returns
synthetic logprobs in the same shape the real server produces, so the whole
logging path, the event payloads, and the tracker's JSON parsing can be
finished and tested on a laptop.

```bash
pip install openai pyyaml         # that's all the mock needs
python llm/client.py              # streams, logs, prints per-token confidence
python llm/tracker.py             # JSON slots for several conversations
```

Only start a paid instance once those both pass.

---

## Real runs: any provider

### 0. Secrets

Never in the repo. Two environment variables:

```bash
export HF_TOKEN=hf_...            # required for gated models, see table below
export VLLM_API_KEY=...           # optional; set it if the port is public
```

### 1. Install

Either install into the instance:

```bash
pip install -r requirements.txt
```

Or skip the install entirely by using vLLM's own image, which is what we'll
build on in Week 2:

```bash
docker run --gpus all -p 8000:8000 \
  -e HF_TOKEN=$HF_TOKEN \
  -v /workspace/hf-cache:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --dtype bfloat16 --max-model-len 8192 --max-logprobs 20
```

### 2. Start the server

```bash
python llm/serve.py                     # reads every flag from configs/config.yaml
python llm/serve.py --print-only        # show the command without running it
VOICE_RAG_MODEL=qwen3_8b python llm/serve.py
```

First start downloads ~16 GB. Point `llm.serve.download_dir` at a persistent
volume so a destroyed instance doesn't mean downloading it again.

### 3. Verify the logprobs — this is the actual gate

```bash
VOICE_RAG_LLM_BACKEND=vllm \
VOICE_RAG_LLM_BASE_URL=http://localhost:8000/v1 \
python llm/client.py
```

You should see a per-token confidence listing and a written log file. "The
model answered" is not the deliverable; visible, logged confidence numbers
are. If you get a 400 mentioning logprobs, the server was started without
`--max-logprobs` >= `llm.logprobs.top_k`.

### 4. Point the rest of the system at it

```bash
export VOICE_RAG_LLM_BACKEND=vllm
export VOICE_RAG_LLM_BASE_URL=https://<host>:<port>/v1
```

### 5. Shut it down

Billing is per second and nobody remembers at 2am. Stop the instance the
moment a run finishes.

---

## RunPod specifics

- Expose HTTP port `8000` in the pod template. RunPod gives you a proxy URL
  shaped like `https://<pod-id>-8000.proxy.runpod.net` — that becomes
  `VOICE_RAG_LLM_BASE_URL` with `/v1` appended.
- Because that URL is public, set `VLLM_API_KEY` before starting. `serve.py`
  picks it up automatically.
- Attach a network volume and set `llm.serve.download_dir` to a path on it,
  or you re-download the weights on every new pod.
- The pod hostname is regenerated each time, which is why the base URL is an
  environment variable and not a committed setting.

## Azure specifics

- NC-series (A100) or NV-series. Check quota **before** planning around it:
  GPU quota on a new or student subscription is request-gated and approval
  can take days. If we're near a deadline, use RunPod.
- Open port 8000 in the network security group, or tunnel it:
  `ssh -L 8000:localhost:8000 user@host` — which is safer, and then the
  default `http://localhost:8000/v1` just works with no config change.

---

## The three models

All three live in `configs/config.yaml`. Switch with one environment variable:
`VOICE_RAG_MODEL=qwen3_8b`.

| Key | Hugging Face id | Gated | Note |
|-----|-----------------|-------|------|
| `llama31_8b` | `meta-llama/Llama-3.1-8B-Instruct` | yes | Default. Accept the licence early — approval isn't always instant |
| `qwen3_8b` | `Qwen/Qwen3-8B` | no | Downloads immediately. Use if a licence is still pending |
| `mistral7b_v03` | `mistralai/Mistral-7B-Instruct-v0.3` | yes | Accept terms; usually instant. 7B, not 8B |

**Qwen3 gotcha:** it emits a `<think>` block by default, which breaks strict
JSON from the tracker and fills the logprob sequence with reasoning tokens
that aren't part of the answer. The config already disables it via
`chat_template_kwargs.enable_thinking: false`; don't remove that.

**These are fallbacks, not a comparison set.** Experiment 1 must be reported
on one model or the model becomes a confound. Whichever is active when real
data collection begins has to be named in the pre-registration doc first.

---

## Cost discipline

- Develop on `mock`. Rent nothing.
- Boot the GPU, verify, collect, shut down. Don't leave it idling overnight.
- Prefer on-demand over reserved until we know how many hours the experiments
  actually need.
