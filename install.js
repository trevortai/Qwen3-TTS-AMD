const COMMON_DEPS = "transformers==4.57.3 accelerate==1.12.0 gradio librosa soundfile einops onnxruntime sox"

module.exports = {
  run: [
    // 1a. Remove app/ if it exists from a previous attempt
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: { message: "if exist app rmdir /s /q app" }
    },
    {
      when: "{{platform === 'linux'}}",
      method: "shell.run",
      params: { message: "rm -rf app" }
    },

    // 1b. Clone Qwen3-TTS
    {
      method: "shell.run",
      params: { message: "git clone https://github.com/QwenLM/Qwen3-TTS app" }
    },

    // 2. Copy launch script — Windows
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: { message: "copy /Y ..\\launch_amd.py launch_amd.py", path: "app" }
    },

    // 2. Copy launch script — Linux
    {
      when: "{{platform === 'linux'}}",
      method: "shell.run",
      params: { message: "cp ../launch_amd.py launch_amd.py", path: "app" }
    },

    // 3. Ensure Python 3.12 is installed via winget (safe to run if already installed)
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: {
        message: "winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements"
      }
    },

    // 4. Create venv with Python 3.12 — searches common install paths directly
    //    (bypasses conda/py launcher which may not see newly installed Python)
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: {
        message: "powershell -command \"$py = @($env:LOCALAPPDATA+'\\Programs\\Python\\Python312\\python.exe','C:\\Program Files\\Python312\\python.exe','C:\\Python312\\python.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1; if (-not $py) { Write-Error 'Python 3.12 not found. Please restart and try again.'; exit 1 }; Write-Host ('Using: ' + $py); & $py -m venv env\"",
        path: "app"
      }
    },

    // 4. Create venv — Linux (Python 3.12 assumed available)
    {
      when: "{{platform === 'linux'}}",
      method: "shell.run",
      params: { message: "python3.12 -m venv env", path: "app" }
    },

    // 5. Install common deps
    {
      method: "shell.run",
      params: {
        message: `pip install ${COMMON_DEPS}`,
        path: "app",
        venv: "env"
      }
    },

    // 6. Detect GPU and install correct wheels
    {
      method: "shell.run",
      params: {
        message: "python ../install_wheels.py",
        path: "app",
        venv: "env"
      }
    },

    // 7. Install qwen-tts last — torchaudio is now present, no resolver conflict
    {
      method: "shell.run",
      params: {
        message: "pip install -e . --no-deps",
        path: "app",
        venv: "env"
      }
    },

    // 8. Done
    {
      method: "notify",
      params: {
        message: "Qwen3-TTS installed successfully. Click Start to launch."
      }
    }
  ]
}
