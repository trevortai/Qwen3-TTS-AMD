"""
Detects GPU and installs the correct PyTorch + ROCm wheels.
Runs inside the venv — called by install.js as a single step.
"""
import subprocess
import sys
import platform


ROCM_BASE_WIN   = "https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1"
ROCM_BASE_LINUX = "https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.1"

ROCM_SDK_WIN = [
    f"{ROCM_BASE_WIN}/rocm_sdk_core-7.2.1-py3-none-win_amd64.whl",
    f"{ROCM_BASE_WIN}/rocm_sdk_devel-7.2.1-py3-none-win_amd64.whl",
    f"{ROCM_BASE_WIN}/rocm_sdk_libraries_custom-7.2.1-py3-none-win_amd64.whl",
]

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

APU_KEYWORDS  = ["780m", "800m", "890m", "880m", "radeon 800", "strix", "phoenix", "hawk point", "ryzen ai max"]


def pip(*args):
    result = subprocess.run([sys.executable, "-m", "pip"] + list(args))
    if result.returncode != 0:
        print(f"pip {' '.join(args[:2])} failed with exit code {result.returncode}")
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

    # Write gpu_type.txt for start.js to read
    with open("gpu_type.txt", "w") as f:
        f.write(gpu)

    print(f"\nDetected GPU type: {gpu} | Platform: {os_name}\n")

    if gpu in ("amd_dgpu", "amd_apu") and os_name == "Windows":
        # Step 1: Install ROCm SDK
        print("Installing ROCm SDK...")
        pip("install", "--no-cache-dir", *ROCM_SDK_WIN)

        # Step 2: Install PyTorch wheels with --no-deps to skip rocm[libraries]==7.2.1
        # dependency resolution — the SDK is already installed under a different package
        # name (rocm-sdk-libraries-custom) so pip can't match it by name, but it works at runtime
        print("\nInstalling ROCm PyTorch wheels (--no-deps)...")
        pip("install", "--no-cache-dir", "--no-deps", "--force-reinstall",
            *ROCM_WHEELS_WIN)

    elif gpu in ("amd_dgpu", "amd_apu") and os_name == "Linux":
        print("Installing ROCm PyTorch wheels (Linux)...")
        pip("install", "--no-cache-dir", "--force-reinstall", *ROCM_WHEELS_LINUX)

        print("\nPinning numpy for Linux ROCm compatibility...")
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

    print("\nPinning numpy (2.x incompatible with ROCm wheels)...")
    pip("install", "numpy==1.26.4")

    # Verify torchaudio installed — use subprocess for fresh Python process
    # (ROCm DLLs only load correctly in a new process after SDK installation)
    result = subprocess.run(
        [sys.executable, "-c", "import torchaudio; print('torchaudio OK')"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"\nERROR: torchaudio failed to import: {result.stderr}")
        sys.exit(1)
    print(f"\n{result.stdout.strip()}")

    print("\nWheel installation complete.")


if __name__ == "__main__":
    main()
