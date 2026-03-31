# Qwen3-TTS (AMD GPU) — Pinokio App

One-click installer for [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) on AMD GPUs via ROCm on Windows.

## Supported Hardware

| Hardware | Support |
|---|---|
| AMD Radeon RX 7000 series (RDNA 3) | ✅ |
| AMD Radeon RX 9000 series (RDNA 4) | ✅ |
| AMD Radeon AI PRO (RDNA 4) | ✅ |
| AMD Ryzen AI 300 APU (Strix) | ✅ |
| AMD Ryzen AI MAX APU (Strix Halo) | ✅ |
| NVIDIA (CUDA fallback) | ✅ |
| CPU only | ✅ (slow) |

## Requirements

- Windows 11
- Python 3.12
- AMD Adrenalin driver 26.2.2 or later (for ROCm support)
- [Pinokio](https://pinokio.computer)

## Install

1. Open Pinokio → Download
2. Paste this repo URL
3. Click **Install** then **Start**

## Optimizations (AMD only)

- `MIOPEN_GEMM_ENFORCE_BACKEND=hipblaslt` — forces faster GEMM solver (~3x speedup)
- `torch.compile(mode="reduce-overhead")` — reduces kernel launch overhead
- GPU keepalive thread — prevents AMD idle downclocking between requests
- Model pre-warmed at startup — first request is fast

## Performance (AMD Radeon AI PRO R9700)

| Setup | Inference time |
|---|---|
| Baseline (cold) | ~67s |
| Baseline (warm) | ~32s |
| With optimizations | ~11-13s |

## Credits

- [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) — original model and code
- GPU keepalive approach inspired by [dingausmwald/Qwen3-TTS-Openai-Fastapi](https://github.com/dingausmwald/Qwen3-TTS-Openai-Fastapi)
