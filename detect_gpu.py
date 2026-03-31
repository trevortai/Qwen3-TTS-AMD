"""
GPU detection script for Qwen3-TTS installer.
Outputs one of: amd_dgpu | amd_apu | nvidia | cpu
"""
import subprocess
import sys


def get_gpu_names():
    try:
        result = subprocess.run(
            ["powershell", "-command",
             "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.lower()
    except Exception:
        return ""


def detect():
    gpus = get_gpu_names()

    has_nvidia = "nvidia" in gpus
    has_amd = "amd" in gpus or "radeon" in gpus

    if not has_amd and not has_nvidia:
        print("cpu")
        return

    if has_nvidia and not has_amd:
        print("nvidia")
        return

    if has_amd:
        # Ryzen AI APUs show up as "radeon 800m", "radeon 780m", "radeon 890m"
        # or "ryzen ai" in the name — discrete cards show "rx 7xxx", "rx 9xxx", "radeon ai pro"
        apu_keywords = ["780m", "800m", "890m", "880m", "radeon 800", "strix", "phoenix", "hawk point", "ryzen ai max"]
        is_apu = any(k in gpus for k in apu_keywords)
        print("amd_apu" if is_apu else "amd_dgpu")
        return

    print("cpu")


if __name__ == "__main__":
    detect()
