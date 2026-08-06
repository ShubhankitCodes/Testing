"""
serve.py — start the vLLM server, reproducibly, on any provider.

Cloud GPU instances get created and destroyed. If the launch command lives
only in someone's shell history, the setup is lost the moment the pod dies —
which is why llm/README.md insists the setup be written down rather than
hand-run once. This file is that record, and it reads every flag from
configs/config.yaml so the command can't drift from what the rest of the
system thinks it's talking to.

Nothing here is provider-specific. RunPod, Azure, or any box with a big
enough card runs the identical command; only the environment around it
differs (see llm/SETUP.md).

Usage, on the GPU box:
    python llm/serve.py                  # start it
    python llm/serve.py --print-only     # just show the command
    VOICE_RAG_MODEL=qwen3_8b python llm/serve.py
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from llm.config import load_config


def build_command(cfg: dict) -> list:
    """Turn the config into the exact `vllm serve` argv."""
    serve = cfg.get("serve") or {}
    lp = cfg.get("logprobs") or {}

    top_k = int(lp.get("top_k", 1))
    max_logprobs = int(serve.get("max_logprobs", 20))
    if top_k > max_logprobs:
        # Requests would come back as a 400 at generation time, which is a
        # confusing way to discover a config mismatch. Fail here instead.
        raise ValueError(
            f"llm.logprobs.top_k ({top_k}) exceeds llm.serve.max_logprobs "
            f"({max_logprobs}). Raise max_logprobs in configs/config.yaml."
        )

    cmd = [
        "vllm",
        "serve",
        cfg["model"],
        "--host",
        str(serve.get("host", "0.0.0.0")),
        "--port",
        str(serve.get("port", 8000)),
        # bfloat16, not a quantized dtype: the logprobs are the measurement
        # instrument for Experiment 1, and quantization shifts the output
        # distribution we are trying to measure.
        "--dtype",
        str(serve.get("dtype", "bfloat16")),
        "--max-model-len",
        str(serve.get("max_model_len", 8192)),
        "--gpu-memory-utilization",
        str(serve.get("gpu_memory_utilization", 0.90)),
        # Without this, top_logprobs requests above the server's default
        # ceiling are rejected. This is the flag that makes this role possible.
        "--max-logprobs",
        str(max_logprobs),
    ]

    download_dir = serve.get("download_dir")
    if download_dir:
        # Point this at a persistent volume so a destroyed pod doesn't mean
        # re-downloading 16 GB of weights.
        cmd += ["--download-dir", str(download_dir)]

    # Only sent if the operator set one. vLLM leaves the endpoint open
    # otherwise, which is fine on a private network and not fine on a pod
    # with a public proxy URL.
    key_env = (cfg.get("server") or {}).get("api_key_env", "VLLM_API_KEY")
    if os.environ.get(key_env):
        cmd += ["--api-key", os.environ[key_env]]

    return cmd


def preflight(cfg: dict) -> bool:
    """Catch the two things that actually go wrong, before burning GPU time."""
    ok = True

    if shutil.which("vllm") is None:
        print("[serve] `vllm` is not on PATH. pip install -r requirements.txt")
        print("        (vLLM needs a CUDA GPU - it will not install usefully on a laptop.)")
        ok = False

    if cfg.get("model_gated") and not os.environ.get("HF_TOKEN"):
        print(
            f"[serve] {cfg['model']} is gated on Hugging Face and HF_TOKEN is "
            f"not set. Accept the licence on the model page, then:"
        )
        print("        export HF_TOKEN=hf_...")
        print(f"        Or switch model: VOICE_RAG_MODEL=qwen3_8b (ungated)")
        ok = False

    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="print the command and exit, without starting anything",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="start even if the preflight checks fail",
    )
    args = parser.parse_args()

    cfg = load_config()
    cmd = build_command(cfg)

    print(f"model       : {cfg['model']}  (key: {cfg['model_key']})")
    print(f"gated       : {cfg['model_gated']}")
    print(f"listening on: {cfg['serve']['host']}:{cfg['serve']['port']}")
    print(f"logprobs    : up to {cfg['logprobs']['top_k']} per token\n")
    print("  " + " ".join(cmd) + "\n")

    if args.print_only:
        return 0
    if not args.skip_preflight and not preflight(cfg):
        print("\n[serve] preflight failed - not starting. --skip-preflight to override.")
        return 1

    print("[serve] starting. First run downloads the weights (~16 GB), so give")
    print("        it a few minutes before the health check passes.")
    print("[serve] verify from another shell with: python llm/client.py\n")
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\n[serve] stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
