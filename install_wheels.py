"""
Detects GPU and installs the correct PyTorch wheels.

dGPU (RDNA 3/4):    Standard ROCm 7.2.1 wheels — no SDK needed
APU (Strix Halo):   Nightly gfx1151 index — self-contained, no SDK needed
NVIDIA:             CUDA 12.4 wheels
CPU:                CPU-only wheels
"""
import os
import subprocess
import sys
import platform

ROCM_BASE_WIN   = "https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1"
ROCM_BASE_LINUX = "https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.1"

ROCM_WHEELS_WIN = [
    f"{ROCM_BASE_WIN}/torch-2.9.1+rocm7.2.1-cp312-cp312-win_amd64.whl",
    f"{ROCM_BASE_WIN}/torchaudio-2.9.1+rocm7.2.1-cp312-cp312-win_amd64.whl",
    f"{ROCM_BASE_WIN}/torchvision-0.24.1+rocm7.2.1-cp312-cp312-win_amd64.whl",
]

ROCM_WHEELS_LINUX = [
    f"{ROCM_BASE_LINUX}/torch-2.9.1+rocm7.2.1.lw.gitff65f5bc-cp312-cp312-linux_x86_64.whl",
    f"{ROCM_BASE_LINUX}/torchaudio-2.9.0+rocm7.2.1.gite3c6ee2b-cp312-cp312-linux_x86_64.whl",
    f"{ROCM_BASE_LINUX}/torchvision-0.24.0+rocm7.2.1.gitb919bd0c-cp312-cp312-linux_x86_64.whl",
    f"{ROCM_BASE_LINUX}/triton-3.5.1+rocm7.2.1.gita272dfa8-cp312-cp312-linux_x86_64.whl",
]

APU_KEYWORDS = ["780m", "800m", "890m", "880m", "radeon 800", "strix", "phoenix", "hawk point", "ryzen ai max"]


def pip(*args):
    result = subprocess.run([sys.executable, "-m", "pip"] + list(args))
    if result.returncode != 0:
        print(f"\npip {' '.join(args[:3])} failed with exit code {result.returncode}")
        sys.exit(result.returncode)


def get_gpus():
    try:
        if platform.system() == "Windows":
            r = subprocess.run(
                ["powershell", "-command",
                 "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=10)
            return r.stdout.lower()
        else:
            r = subprocess.run(["lspci"], capture_output=True, text=True, timeout=10)
            lines = [l for l in r.stdout.lower().splitlines()
                     if any(k in l for k in ["vga", "display", "3d controller"])]
            return " ".join(lines)
    except Exception:
        return ""


def detect_gpu():
    gpus = get_gpus()
    has_amd    = "amd" in gpus or "radeon" in gpus or "advanced micro devices" in gpus
    has_nvidia = "nvidia" in gpus

    if has_amd:
        is_apu = any(k in gpus for k in APU_KEYWORDS)
        return "amd_apu" if is_apu else "amd_dgpu"
    if has_nvidia:
        return "nvidia"
    return "cpu"


def main():
    os_name = platform.system()
    gpu = detect_gpu()

    with open("gpu_type.txt", "w") as f:
        f.write(gpu)

    print(f"\nDetected GPU type: {gpu} | Platform: {os_name}\n")

    if gpu == "amd_dgpu" and os_name == "Windows":
        # Standard ROCm 7.2.1 wheels — confirmed working on RDNA 3/4 dGPU
        print("Installing ROCm PyTorch wheels (dGPU)...")
        pip("install", "--no-cache-dir", "--force-reinstall", *ROCM_WHEELS_WIN)

    elif gpu == "amd_apu" and os_name == "Windows":
        # Strix Halo / Ryzen APU — use nightly gfx1151 index (self-contained, no SDK needed)
        print("Installing ROCm PyTorch wheels (APU / Strix Halo — nightly gfx1151)...")
        pip("install", "--pre", "--force-reinstall",
            "--index-url", "https://rocm.nightlies.amd.com/v2/gfx1151/",
            "torch", "torchaudio", "torchvision")

    elif gpu in ("amd_dgpu", "amd_apu") and os_name == "Linux":
        print("Installing ROCm PyTorch wheels (Linux)...")
        pip("install", "--no-cache-dir", "--force-reinstall", *ROCM_WHEELS_LINUX)
        pip("install", "numpy==1.26.4")

    elif gpu == "nvidia":
        print("Installing CUDA PyTorch wheels...")
        pip("install", "--force-reinstall",
            "--index-url", "https://download.pytorch.org/whl/cu124",
            "torch", "torchaudio", "torchvision")

    else:
        print("No AMD/NVIDIA GPU detected — installing CPU-only PyTorch...")
        pip("install", "--force-reinstall",
            "--index-url", "https://download.pytorch.org/whl/cpu",
            "torch", "torchaudio", "torchvision")

    pip("install", "numpy==1.26.4")
    print("\nWheel installation complete.")


if __name__ == "__main__":
    main()
