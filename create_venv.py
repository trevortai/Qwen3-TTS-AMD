"""
Creates a Python 3.12 venv by reading the install path from the Windows Registry.
This works even when the py launcher or PATH hasn't refreshed after a new install.
"""
import subprocess
import sys
import os


def find_python312_windows():
    """Look up Python 3.12 install path from Windows Registry."""
    try:
        import winreg
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key = winreg.OpenKey(root, r"SOFTWARE\Python\PythonCore\3.12\InstallPath")
                path, _ = winreg.QueryValueEx(key, "ExecutablePath")
                winreg.CloseKey(key)
                if os.path.exists(path):
                    return path
            except FileNotFoundError:
                continue
    except ImportError:
        pass

    # Fallback: check common install paths
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python312", "python.exe"),
        r"C:\Program Files\Python312\python.exe",
        r"C:\Python312\python.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def main():
    python312 = find_python312_windows()

    if not python312:
        print("ERROR: Python 3.12 not found.")
        print("Please restart Pinokio and try installing again.")
        print("If the problem persists, install Python 3.12 manually from https://www.python.org/downloads/")
        sys.exit(1)

    print(f"Found Python 3.12: {python312}")

    venv_path = os.path.join(os.getcwd(), "env")
    print(f"Creating venv at: {venv_path}")

    # Use the py launcher (Microsoft-signed, trusted by app control policies)
    # rather than calling the Python 3.12 executable directly
    result = subprocess.run(["py", "-3.12", "-m", "venv", venv_path])
    if result.returncode != 0:
        # Fallback: try calling the executable directly
        print("py launcher failed, trying direct path...")
        result = subprocess.run([python312, "-m", "venv", venv_path])
    if result.returncode != 0:
        print("ERROR: Failed to create venv.")
        sys.exit(1)

    print("Venv created successfully.")


if __name__ == "__main__":
    main()
