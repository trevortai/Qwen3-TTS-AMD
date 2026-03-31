"""
GPU detection script for Qwen3-TTS installer.
Outputs one of: amd_dgpu | amd_apu | nvidia | cpu
Supports Windows and Linux.
"""
import subprocess
import sys
import platform


APU_KEYWORDS = ["780m", "800m", "890m", "880m", "radeon 800", "strix", "phoenix", "hawk point", "ryzen ai max"]


def get_gpu_names_windows():
    try:
        result = subprocess.run(
            ["powershell", "-command",
             "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.lower()
    except Exception:
        return ""


def get_gpu_names_linux():
    try:
        result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=10)
        # Filter to VGA / Display / 3D controller lines
        lines = [l for l in result.stdout.lower().splitlines()
                 if any(k in l for k in ["vga", "display", "3d controller"])]
        return " ".join(lines)
    except Exception:
        return ""


def detect():
    os_name = platform.system()

    if os_name == "Windows":
        gpus = get_gpu_names_windows()
    elif os_name == "Linux":
        gpus = get_gpu_names_linux()
    else:
        print("cpu")
        return

    has_nvidia = "nvidia" in gpus
    has_amd = "amd" in gpus or "radeon" in gpus or "advanced micro devices" in gpus

    if not has_amd and not has_nvidia:
        print("cpu")
        return

    if has_nvidia and not has_amd:
        print("nvidia")
        return

    if has_amd:
        is_apu = any(k in gpus for k in APU_KEYWORDS)
        print("amd_apu" if is_apu else "amd_dgpu")
        return

    print("cpu")


if __name__ == "__main__":
    detect()
