const ROCM_BASE = "https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1"
const ROCM_WHEELS = [
  `${ROCM_BASE}/torch-2.9.1+rocm7.2.1-cp312-cp312-win_amd64.whl`,
  `${ROCM_BASE}/torchaudio-2.9.1+rocm7.2.1-cp312-cp312-win_amd64.whl`,
  `${ROCM_BASE}/torchvision-0.24.1+rocm7.2.1-cp312-cp312-win_amd64.whl`,
].join(" ")

const CUDA_WHEELS = "--index-url https://download.pytorch.org/whl/cu124 torch torchaudio torchvision"
const CPU_WHEELS  = "--index-url https://download.pytorch.org/whl/cpu torch torchaudio torchvision"

const COMMON_DEPS = "transformers==4.57.3 accelerate==1.12.0 gradio librosa soundfile einops onnxruntime sox"

module.exports = {
  run: [
    // 1. Clone Qwen3-TTS
    {
      method: "shell.run",
      params: { message: "git clone https://github.com/QwenLM/Qwen3-TTS app" }
    },

    // 2. Create venv with Python 3.12
    {
      method: "shell.run",
      params: { message: "python -m venv env", path: "app" }
    },

    // 3. Copy launch script into app folder
    {
      method: "shell.run",
      params: { message: "copy ..\\launch_amd.py launch_amd.py", path: "app" }
    },

    // 4. Detect GPU and write result to gpu_type.txt
    {
      method: "shell.run",
      params: {
        message: "python ../detect_gpu.py > gpu_type.txt",
        path: "app",
        venv: "env"
      }
    },

    // 5. Read GPU type
    {
      method: "fs.read",
      params: { path: "app/gpu_type.txt" }
    },

    // 6. Install correct PyTorch wheels based on GPU type
    {
      method: "shell.run",
      params: {
        // input.data is the output of fs.read (gpu_type.txt contents)
        message: `{{
          const gpu = input.data.trim();
          if (gpu === 'amd_dgpu' || gpu === 'amd_apu') {
            return 'pip install --no-cache-dir ${ROCM_WHEELS}';
          } else if (gpu === 'nvidia') {
            return 'pip install ${CUDA_WHEELS}';
          } else {
            return 'pip install ${CPU_WHEELS}';
          }
        }}`,
        path: "app",
        venv: "env"
      }
    },

    // 7. Install Qwen3-TTS and remaining deps (no-deps to protect torch wheels)
    {
      method: "shell.run",
      params: {
        message: `pip install -e . --no-deps && pip install ${COMMON_DEPS}`,
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
