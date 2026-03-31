"""
Optimized Gradio launch script for Qwen3-TTS on AMD GPU (ROCm)
- HIP/MIOpen env vars set by start.js before this script runs
- torch.compile with reduce-overhead mode
- Pre-warms model before serving requests
- GPU keepalive thread prevents AMD idle downclocking
"""
import os
import sys
import time
import threading

# HIP/MIOpen env vars are set by start.js before this script runs.
# They must be in the environment before torch is imported to take effect.
import torch

from qwen_tts import Qwen3TTSModel
from qwen_tts.cli.demo import build_demo

MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
PORT = 8000
KEEPALIVE_INTERVAL = int(os.environ.get("GPU_KEEPALIVE_INTERVAL", 15))

# Determine device
if torch.cuda.is_available():
    DEVICE = "cuda:0"
    gpu_name = torch.cuda.get_device_name(0).lower()
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {vram:.1f} GB")
    USE_GPU = True
else:
    DEVICE = "cpu"
    USE_GPU = False
    print("WARNING: No GPU detected — running on CPU.")
    print("Inference will be very slow (several minutes per request).")


def gpu_keepalive(interval: int):
    """Periodically runs a small matmul to prevent AMD GPU idle downclocking."""
    dummy = torch.ones(16, 16, device=DEVICE, dtype=torch.bfloat16)
    while True:
        time.sleep(interval)
        try:
            _ = dummy @ dummy
            torch.cuda.synchronize()
        except Exception:
            pass


# Start GPU keepalive for AMD only (prevents DPM idle downclocking)
if USE_GPU and ("amd" in gpu_name or "radeon" in gpu_name):
    print(f"Starting GPU keepalive (interval: {KEEPALIVE_INTERVAL}s)...")
    t = threading.Thread(target=gpu_keepalive, args=(KEEPALIVE_INTERVAL,), daemon=True)
    t.start()

print(f"\nLoading {MODEL}...")
tts = Qwen3TTSModel.from_pretrained(
    MODEL,
    device_map=DEVICE,
    dtype=torch.bfloat16 if USE_GPU else torch.float32,
    attn_implementation="sdpa",
)

if USE_GPU:
    print("Compiling model (reduce-overhead)...")
    tts.model = torch.compile(tts.model, mode="reduce-overhead", dynamic=True)
    print("Pre-warming model (first request will now be fast)...")
    t0 = time.time()
    tts.generate_custom_voice(
        text="Warming up.",
        language="english",
        speaker="ryan",
        instruct="",
    )
    print(f"Warmup done in {time.time()-t0:.1f}s\n")
else:
    print("Skipping warmup on CPU.\n")

print(f"Starting Gradio on http://localhost:{PORT}")
demo = build_demo(tts, MODEL, {})
demo.queue(default_concurrency_limit=4).launch(
    server_name="0.0.0.0",
    server_port=PORT,
)
