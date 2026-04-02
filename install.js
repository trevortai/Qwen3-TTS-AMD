const COMMON_DEPS = "transformers==4.57.3 accelerate==1.12.0 gradio librosa soundfile einops onnxruntime sox"

module.exports = {
  run: [
    // 1. Clone Qwen3-TTS
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

    // 3. Install common deps
    //    venv_python: "3.12" tells Pinokio to create the venv with Python 3.12
    //    Pinokio manages Python versions automatically — no manual install needed
    {
      method: "shell.run",
      params: {
        message: `pip install ${COMMON_DEPS}`,
        path: "app",
        venv: "env",
        venv_python: "3.12"
      }
    },

    // 4. Detect GPU and install correct wheels
    {
      method: "shell.run",
      params: {
        message: "python ../install_wheels.py",
        path: "app",
        venv: "env"
      }
    },

    // 5. Install qwen-tts last — torchaudio is now present, no resolver conflict
    {
      method: "shell.run",
      params: {
        message: "pip install -e . --no-deps",
        path: "app",
        venv: "env"
      }
    },

    // 6. Done
    {
      method: "notify",
      params: {
        message: "Qwen3-TTS installed successfully. Click Start to launch."
      }
    }
  ]
}
