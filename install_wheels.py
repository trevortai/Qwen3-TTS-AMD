"""
Detects GPU and installs the correct PyTorch wheels.

dGPU (RDNA 3/4):    ROCm 7.2.1 — SDK + rocm-7.2.1.tar.gz + torch wheels (AMD installrad docs)
APU (Strix Halo):   ROCm 7.2.1 — SDK + rocm-7.2.1.tar.gz + torch wheels (AMD installryz docs)
NVIDIA:             CUDA 12.4 wheels
CPU:                CPU-only wheels
"""
import subprocess
import sys
import platform

ROCM_BASE_WIN   = "https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1"
ROCM_BASE_LINUX = "https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.1"


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

    py_ver = platform.python_version()
    print(f"\nDetected GPU type: {gpu} | Platform: {os_name} | Python: {py_ver}\n")

    if sys.version_info < (3, 12):
        print(f"ERROR: Python 3.12 is required for ROCm wheels. Currently using Python {py_ver}.")
        print("Please ensure Python 3.12 is installed and try again.")
        sys.exit(1)

    if gpu in ("amd_dgpu", "amd_apu") and os_name == "Windows":
        # AMD Windows — same process for both dGPU and APU per AMD docs
        # rocm-7.2.1.tar.gz provides the rocm Python package (rocm_sdk module) torch needs
        print(f"Installing ROCm SDK ({gpu})...")
        pip("install", "--no-cache-dir",
            f"{ROCM_BASE_WIN}/rocm_sdk_core-7.2.1-py3-none-win_amd64.whl",
            f"{ROCM_BASE_WIN}/rocm_sdk_devel-7.2.1-py3-none-win_amd64.whl",
            f"{ROCM_BASE_WIN}/rocm_sdk_libraries_custom-7.2.1-py3-none-win_amd64.whl",
            f"{ROCM_BASE_WIN}/rocm-7.2.1.tar.gz")

        print(f"\nInstalling ROCm PyTorch wheels ({gpu})...")
        pip("install", "--no-cache-dir", "--no-deps", "--force-reinstall",
            f"{ROCM_BASE_WIN}/torch-2.9.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl",
            f"{ROCM_BASE_WIN}/torchaudio-2.9.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl",
            f"{ROCM_BASE_WIN}/torchvision-0.24.1%2Brocm7.2.1-cp312-cp312-win_amd64.whl")

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
