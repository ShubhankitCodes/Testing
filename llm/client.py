"""
client.py — talk to the language model, and log what it was confident about.

This is the file the rest of the system calls. It does two jobs:

1. Send a prompt to an ~8B instruct model and stream the answer back.
2. Capture the per-token logprobs and write them into the frozen event log.

Job 2 is the actual deliverable of this role (llm/README.md). A later
experiment tests whether the model's own uncertainty predicts when it needs
to look something up. If the confidence numbers aren't exposed and logged,
that experiment cannot happen at all. Getting answers out is the easy half.

Why streaming and not a single blocking call
--------------------------------------------
The schema has a distinct `llm_first_token` event, and Time To First Audio is
the project's headline metric. A non-streaming call hands you the whole answer
at once, so any "first token" timestamp you wrote would be fiction. We stream
and stamp the first token the moment it actually arrives.

Two backends, one interface
---------------------------
`MockClient` returns a canned answer with synthetic logprobs in the exact
shape the real server produces. It needs no GPU, no network, and no money, so
the entire logging path can be built and tested on a laptop. `VLLMClient`
talks to a real vLLM server. Both satisfy the same interface, so switching is
a config change (llm.backend) and nothing else moves.

Run it:
    python llm/client.py            # mock, writes logs/conv_llm_demo.jsonl
    VOICE_RAG_LLM_BACKEND=vllm python llm/client.py
"""

import json
import math
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# eventlog/ and configs/ are sibling top-level folders, not subpackages of
# llm/. Same reasoning as pipeline/spine.py: adding the repo root here means
# both `python llm/client.py` and `python -m llm.client` work.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from eventlog.log_writer import LogWriter, now_ms
from llm.config import api_key, load_config


# ---------------------------------------------------------------------------
# What a generation gives you back
# ---------------------------------------------------------------------------
@dataclass
class TokenLogprob:
    """One output token and how confident the model was in it.

    logprob is a natural log of a probability, so it is always <= 0.
    -0.01 is near-certain; -3.0 means the model was guessing.
    """

    token: str
    logprob: float


@dataclass
class Generation:
    """Everything one model call produced, including the timing."""

    text: str
    tokens: list = field(default_factory=list)  # list[TokenLogprob]
    model: str = ""
    first_token_ms: int = None  # t_ms of the first token, shared clock
    final_ms: int = None  # t_ms when the answer completed
    start_ms: int = None  # t_ms when we sent the request

    @property
    def ttft_ms(self):
        """Time to first token, in ms. The LLM's share of the TTFA budget."""
        if self.first_token_ms is None or self.start_ms is None:
            return None
        return self.first_token_ms - self.start_ms

    @property
    def mean_logprob(self):
        """Average confidence across the answer. Higher (closer to 0) = surer."""
        if not self.tokens:
            return None
        return sum(t.logprob for t in self.tokens) / len(self.tokens)

    @property
    def min_logprob(self):
        """The single least-confident token. Often the interesting one."""
        if not self.tokens:
            return None
        return min(t.logprob for t in self.tokens)

    @property
    def perplexity(self):
        """exp(-mean logprob). A conventional summary of "how unsure overall"."""
        m = self.mean_logprob
        return math.exp(-m) if m is not None else None

    def logprob_dicts(self):
        """The per-token list, JSON-ready for the event payload."""
        return [{"token": t.token, "logprob": round(t.logprob, 6)} for t in self.tokens]


# ---------------------------------------------------------------------------
# Logging — the part that must match eventlog/schema.md exactly
# ---------------------------------------------------------------------------
# The schema is FROZEN and its event-type list is closed, so the confidence
# numbers go inside the `payload` of the two events that already exist rather
# than into a new event type of our own invention. The schema defines payload
# as "an object with details specific to that event type", which is exactly
# what this is — additive, and it breaks nothing downstream.
#
#   llm_first_token  payload: {token, logprob}
#   llm_final        payload: {text, logprobs: [...], mean_logprob, ...}
#
# Renya owns the schema: confirm this reading before it goes in a PR.


def _log_first_token(log_writer, turn_id, token: str, logprob):
    payload = {"token": token}
    if logprob is not None:
        payload["logprob"] = round(logprob, 6)
    log_writer.log_event("system", "llm_first_token", payload, turn_id)


def _log_final(log_writer, turn_id, gen: Generation, log_full: bool):
    payload = {
        "text": gen.text,
        "model": gen.model,
        "n_tokens": len(gen.tokens),
    }
    if gen.tokens:
        payload["mean_logprob"] = round(gen.mean_logprob, 6)
        payload["min_logprob"] = round(gen.min_logprob, 6)
        payload["perplexity"] = round(gen.perplexity, 4)
        if log_full:
            # Verbose on purpose. These logs are the paper's raw data; a
            # summary statistic we can always recompute, a discarded
            # per-token sequence we cannot.
            payload["logprobs"] = gen.logprob_dicts()
    if gen.ttft_ms is not None:
        payload["ttft_ms"] = gen.ttft_ms
    log_writer.log_event("system", "llm_final", payload, turn_id)


# ---------------------------------------------------------------------------
# The real client
# ---------------------------------------------------------------------------
class VLLMClient:
    """
    Talks to a vLLM server over its OpenAI-compatible API.

    The server must have been started with --max-logprobs >= the top_k in
    config, or every request comes back as a 400. llm/serve.py handles that.
    """

    def __init__(self, cfg: dict = None):
        self.cfg = cfg or load_config()
        server = self.cfg.get("server") or {}

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - environment problem
            raise RuntimeError(
                "The `openai` package is needed to talk to vLLM's "
                "OpenAI-compatible endpoint. It's in requirements.txt: "
                "pip install -r requirements.txt"
            ) from exc

        self.model = self.cfg["model"]
        self.extra_body = self.cfg.get("extra_body") or {}
        self._client = OpenAI(
            base_url=server.get("base_url", "http://localhost:8000/v1"),
            api_key=api_key(self.cfg),
            timeout=server.get("request_timeout_s", 120),
        )

    def health_check(self) -> bool:
        """Is a server actually there, and is it serving the model we expect?"""
        try:
            served = [m.id for m in self._client.models.list().data]
        except Exception as exc:
            print(f"[llm] cannot reach the server: {exc}")
            return False
        if self.model not in served:
            print(f"[llm] server is up but serves {served}, not {self.model}")
            return False
        return True

    def generate(self, messages, log_writer=None, turn_id=None, **overrides):
        """
        Stream one completion. Returns a Generation.

        Pass log_writer + turn_id to emit llm_first_token and llm_final. Leave
        them out for calls that shouldn't appear in the conversation timeline
        — the state tracker is the case that matters, since its internal model
        call is not the assistant speaking.
        """
        gen_cfg = dict(self.cfg.get("generation") or {})
        gen_cfg.update(overrides)
        lp_cfg = self.cfg.get("logprobs") or {}
        want_logprobs = bool(lp_cfg.get("enabled", True))

        request = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": gen_cfg.get("max_tokens", 256),
            "temperature": gen_cfg.get("temperature", 0.2),
            "top_p": gen_cfg.get("top_p", 0.9),
        }
        if want_logprobs:
            # The whole reason we self-host. A closed API will not give us these.
            request["logprobs"] = True
            request["top_logprobs"] = lp_cfg.get("top_k", 1)
        if self.extra_body:
            request["extra_body"] = self.extra_body

        gen = Generation(text="", model=self.model, start_ms=now_ms())
        pieces = []

        stream = self._client.chat.completions.create(**request)
        for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = getattr(choice.delta, "content", None) or ""

            # logprobs arrive on the chunk alongside the text. Some chunks
            # (role headers, the final stop chunk) carry neither, hence the
            # defensive unwrapping.
            entries = []
            lp = getattr(choice, "logprobs", None)
            if lp is not None and getattr(lp, "content", None):
                entries = lp.content

            for entry in entries:
                gen.tokens.append(TokenLogprob(entry.token, entry.logprob))

            if gen.first_token_ms is None and (delta or entries):
                # Stamp it here, at the moment the first content actually
                # lands, not after the stream finishes.
                gen.first_token_ms = now_ms()
                if log_writer is not None:
                    first_tok = entries[0].token if entries else delta
                    first_lp = entries[0].logprob if entries else None
                    _log_first_token(log_writer, turn_id, first_tok, first_lp)

            if delta:
                pieces.append(delta)

        gen.text = "".join(pieces)
        gen.final_ms = now_ms()

        if log_writer is not None:
            _log_final(log_writer, turn_id, gen, bool(lp_cfg.get("log_full", True)))
        return gen


# ---------------------------------------------------------------------------
# The mock client
# ---------------------------------------------------------------------------
class MockClient:
    """
    A stand-in that produces the same Generation shape with no GPU.

    This exists for cost control (llm/README.md: "use cheap or free compute
    for development, reserve the paid GPU for real runs"). Everything
    downstream of the model — the payload shape, the JSON parsing in
    tracker.py, the harness reading the logs — can be finished and tested
    before a paid instance is ever started.

    The logprobs are synthetic but deliberately realistic: mostly confident,
    with occasional low-confidence tokens, so code that looks for uncertainty
    has something to find. They are seeded on the prompt, so the same prompt
    always gives the same numbers and tests stay deterministic.
    """

    CANNED_ANSWER = "The pool is open daily from 6 AM until 10 PM."

    def __init__(self, cfg: dict = None):
        self.cfg = cfg or load_config()
        self.model = f"mock:{self.cfg['model']}"
        self.extra_body = {}

    def health_check(self) -> bool:
        return True

    def generate(self, messages, log_writer=None, turn_id=None, **overrides):
        gen_cfg = dict(self.cfg.get("generation") or {})
        gen_cfg.update(overrides)
        lp_cfg = self.cfg.get("logprobs") or {}

        answer = overrides.pop("mock_answer", None) or self.CANNED_ANSWER
        seed = hash(json.dumps(messages, sort_keys=True, default=str)) & 0xFFFFFFFF
        rng = random.Random(seed)

        gen = Generation(text="", model=self.model, start_ms=now_ms())

        # Simulate the server thinking before the first token appears. Real
        # TTFT for an 8B on a single card is roughly this order of magnitude.
        time.sleep(0.09)

        # Split on whitespace, keeping the spaces attached the way a real
        # tokenizer emits them (" pool", not "pool"), and honour max_tokens so
        # a truncated answer behaves the same way here as on the real server.
        raw_tokens = answer.split(" ")[: int(gen_cfg.get("max_tokens", 256))]
        pieces = []
        for i, word in enumerate(raw_tokens):
            tok = word if i == 0 else " " + word
            # Mostly confident, one in six noticeably unsure.
            logprob = -rng.uniform(2.0, 3.5) if rng.random() < 0.17 else -rng.uniform(0.005, 0.45)

            if gen.first_token_ms is None:
                gen.first_token_ms = now_ms()
                if log_writer is not None:
                    _log_first_token(log_writer, turn_id, tok, logprob)

            gen.tokens.append(TokenLogprob(tok, logprob))
            pieces.append(tok)
            time.sleep(0.012)  # per-token decode time

        gen.text = "".join(pieces)
        gen.final_ms = now_ms()

        if log_writer is not None:
            _log_final(log_writer, turn_id, gen, bool(lp_cfg.get("log_full", True)))
        return gen


# ---------------------------------------------------------------------------
# Picking a backend
# ---------------------------------------------------------------------------
def make_client(cfg: dict = None):
    """Return the client the config asks for. The only place backends branch."""
    cfg = cfg or load_config()
    backend = (cfg.get("backend") or "mock").lower()
    if backend == "mock":
        return MockClient(cfg)
    if backend == "vllm":
        return VLLMClient(cfg)
    raise ValueError(f"Unknown llm.backend '{backend}' - expected 'mock' or 'vllm'.")


# ---------------------------------------------------------------------------
# The prompt the assistant answers with
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a hotel phone concierge. Answer the guest's question using only "
    "the reference passages provided. Be brief — one or two sentences, spoken "
    "aloud over a phone call. If the passages do not contain the answer, say "
    "you don't have that information rather than guessing."
)


def build_messages(question: str, passages) -> list:
    """Assemble the RAG prompt from a question and the retrieved passages."""
    if passages:
        context = "\n".join(f"- {p}" for p in passages)
        user = f"Reference passages:\n{context}\n\nGuest question: {question}"
    else:
        user = f"Guest question: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# The spine drop-in
# ---------------------------------------------------------------------------
# Deliberately the same signature as the stub at pipeline/spine.py:138 so
# Renya's swap is one import line and nothing else in the spine moves.
#
# NOTE FOR RENYA: the stub takes only `passages`, but a real model needs the
# user's question too — answering from passages alone isn't possible. The
# `question` argument is keyword-optional so the existing call site keeps
# working today; when you wire this in, pass the transcript through.
_DEFAULT_CLIENT = None


def generate_answer(
    passages: list,
    log_writer: LogWriter,
    turn_id: int,
    question: str = "",
    client=None,
) -> str:
    """Generate the spoken answer, logging llm_first_token and llm_final."""
    global _DEFAULT_CLIENT
    if client is None:
        # Built once and reused: constructing a client opens an HTTP session,
        # and doing that per turn would add latency to the metric we care about.
        if _DEFAULT_CLIENT is None:
            _DEFAULT_CLIENT = make_client()
        client = _DEFAULT_CLIENT

    gen = client.generate(
        build_messages(question, passages), log_writer=log_writer, turn_id=turn_id
    )
    return gen.text


# ---------------------------------------------------------------------------
# Demo — proves the confidence numbers are visible, which is the deliverable
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cfg = load_config()
    print(f"backend : {cfg['backend']}")
    print(f"model   : {cfg['model']}  (key: {cfg['model_key']})")

    client = make_client(cfg)
    if cfg["backend"] == "vllm" and not client.health_check():
        print("\nServer unreachable. Start it with `python llm/serve.py`, or")
        print("run this demo against the mock: VOICE_RAG_LLM_BACKEND=mock")
        sys.exit(1)

    passages = [
        "Pool hours: the pool is open daily from 6:00 AM to 10:00 PM.",
        "The pool deck closes 30 minutes before the pool itself for cleaning.",
    ]
    question = "what time does the pool close"

    writer = LogWriter(conversation_id="conv_llm_demo", log_dir=cfg.get("log_dir", "logs"))
    try:
        gen = client.generate(
            build_messages(question, passages), log_writer=writer, turn_id=1
        )
    finally:
        writer.close()

    print(f"\nanswer  : {gen.text}")
    print(f"TTFT    : {gen.ttft_ms} ms")
    print(f"tokens  : {len(gen.tokens)}")
    print(f"mean lp : {gen.mean_logprob:.4f}   min lp: {gen.min_logprob:.4f}")
    print(f"perplex : {gen.perplexity:.3f}")

    print("\nper-token confidence (this is the thing that must be visible):")
    for t in gen.tokens:
        bar = "#" * max(1, int((t.logprob + 4) / 4 * 30))
        flag = "  <-- unsure" if t.logprob < -2.0 else ""
        print(f"  {t.logprob:8.4f}  {bar:<30} {t.token!r}{flag}")

    print(f"\nlogged to {writer._path}")
    for line in writer._path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event["event_type"].startswith("llm_"):
            keys = list(event["payload"])
            print(f"  t={event['t_ms']:>5} {event['event_type']:<16} payload keys: {keys}")
