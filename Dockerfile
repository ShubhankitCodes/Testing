# Dockerfile — reproducible environment for llm/ (model serving + signals).
#
# Cloud GPU instances get created and destroyed constantly. Anything
# hand-installed on one instance is lost with it, which is why the setup lives
# here rather than in someone's shell history.
#
# Two build targets, one file:
#
#   dev  — CPU only, ~150 MB. Runs the mock backend, the tracker, and the
#          event-log tests. No GPU, no model weights, no cost. This is what
#          you should use for everything except real data collection.
#
#   gpu  — CUDA + vLLM, several GB. Serves the real ~8B model with logprobs
#          exposed. Build and run this only on a machine with a GPU.
#
#   docker build --target dev -t voice-rag-llm:dev .
#   docker build --target gpu -t voice-rag-llm:gpu .
#
# Scope note: this image installs only what llm/ needs (pyyaml, openai). It
# deliberately does NOT install the rest of requirements.txt — faster-whisper,
# sentence-transformers and faiss all pull their own torch builds, which would
# fight with the exact torch vLLM is compiled against and produce an image
# that imports but doesn't run. The combined all-components image is a
# separate piece of work (Renya / Week 2); this one is the llm/ layer it
# should build on.


# An ARG referenced by a FROM must be declared before the first FROM —
# anything declared inside a stage belongs to that stage only and is invisible
# to later FROM lines.
#
# TODO: pin this to a specific tag after the first successful pod run.
# `latest` is convenient now and a reproducibility hole later — the whole
# point of this file is that the environment doesn't drift.
ARG VLLM_VERSION=latest


# ===========================================================================
# dev — CPU, no GPU, no weights
# ===========================================================================
FROM python:3.12-slim AS dev

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VOICE_RAG_LLM_BACKEND=mock

WORKDIR /app

# openai is the client for vLLM's OpenAI-compatible API; pyyaml reads
# configs/config.yaml. Nothing else is needed to run the mock end to end.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir openai pyyaml

# Only the folders llm/ actually imports. Copying the whole repo would
# invalidate this layer every time a teammate edits their own component.
COPY configs/ /app/configs/
COPY eventlog/ /app/eventlog/
COPY llm/ /app/llm/

# Logs are runtime output, mounted or discarded — never baked into the image.
VOLUME ["/app/logs"]

# The base image sets no entrypoint, so CMD stands alone and is easy to
# override: `docker run voice-rag-llm:dev python3 llm/tracker.py`
CMD ["python3", "llm/client.py"]


# ===========================================================================
# gpu — CUDA + vLLM, serves the real model
# ===========================================================================
FROM vllm/vllm-openai:${VLLM_VERSION} AS gpu

# HF_HOME is where weights land. Mount a persistent volume at /models, or
# every new instance re-downloads ~16 GB before it can answer anything.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VOICE_RAG_LLM_BACKEND=vllm \
    HF_HOME=/models

WORKDIR /app

# vLLM and CUDA are already in the base image. Adding only our two client
# libraries keeps us from touching the torch build vLLM is pinned to.
RUN pip install --no-cache-dir openai pyyaml

COPY configs/ /app/configs/
COPY eventlog/ /app/eventlog/
COPY llm/ /app/llm/

RUN mkdir -p /models /app/logs
VOLUME ["/models", "/app/logs"]

EXPOSE 8000

# vllm/vllm-openai ships an ENTRYPOINT that launches the API server directly,
# which would bypass llm/serve.py and therefore all the flags in
# configs/config.yaml — including --max-logprobs, without which the logprob
# requests this whole role exists for come back as a 400. Clear it so CMD
# runs our launcher instead.
ENTRYPOINT []

# Is the server up AND actually answering? start-period is long because the
# first boot downloads the weights.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15m --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# serve.py reads every flag from configs/config.yaml, so the container and
# the client can never disagree about how the model is configured.
# Switch models without rebuilding:  -e VOICE_RAG_MODEL=qwen3_8b
CMD ["python3", "llm/serve.py"]
