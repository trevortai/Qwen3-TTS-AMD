// Wheel sources — all from AMD's official repo.radeon.com
// Windows: https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/
// Linux:   https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.1/

const ROCM_BASE_WIN   = "https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1"
const ROCM_BASE_LINUX = "https://repo.radeon.com/rocm/manylinux/rocm-rel-7.2.1"

const ROCM_WHEELS_WIN = [
  `${ROCM_BASE_WIN}/torch-2.9.1+rocm7.2.1-cp312-cp312-win_amd64.whl`,
  `${ROCM_BASE_WIN}/torchaudio-2.9.1+rocm7.2.1-cp312-cp312-win_amd64.whl`,
  `${ROCM_BASE_WIN}/torchvision-0.24.1+rocm7.2.1-cp312-cp312-win_amd64.whl`,
].join(" ")

const ROCM_WHEELS_LINUX = [
  `${ROCM_BASE_LINUX}/torch-2.9.1+rocm7.2.1.lw.gitff65f5bc-cp312-cp312-linux_x86_64.whl`,
  `${ROCM_BASE_LINUX}/torchaudio-2.9.0+rocm7.2.1.gite3c6ee2b-cp312-cp312-linux_x86_64.whl`,
  `${ROCM_BASE_LINUX}/torchvision-0.24.0+rocm7.2.1.gitb919bd0c-cp312-cp312-linux_x86_64.whl`,
  `${ROCM_BASE_LINUX}/triton-3.5.1+rocm7.2.1.gita272dfa8-cp312-cp312-linux_x86_64.whl`,
].join(" ")

const CUDA_WHEELS   = "--index-url https://download.pytorch.org/whl/cu124 torch torchaudio torchvision"
const CPU_WHEELS    = "--index-url https://download.pytorch.org/whl/cpu torch torchaudio torchvision"
const COMMON_DEPS   = "transformers==4.57.3 accelerate==1.12.0 gradio librosa soundfile einops onnxruntime sox"

module.exports = {
  run: [
    // 1. Clone Qwen3-TTS
    {
      method: "shell.run",
      params: { message: "git clone https://github.com/QwenLM/Qwen3-TTS app" }
    },

    // 2. Create venv (Python 3.12 required)
    {
      method: "shell.run",
      params: { message: "python -m venv env", path: "app" }
    },

    // 3. Copy launch script — Windows
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: { message: "copy ..\\launch_amd.py launch_amd.py", path: "app" }
    },

    // 3. Copy launch script — Linux
    {
      when: "{{platform === 'linux'}}",
      method: "shell.run",
      params: { message: "cp ../launch_amd.py launch_amd.py", path: "app" }
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

    // 6. Install correct PyTorch wheels based on GPU + platform
    {
      method: "shell.run",
      params: {
        message: `{{
          const gpu = input.data.trim();
          if (gpu === 'amd_dgpu' || gpu === 'amd_apu') {
            return platform === 'win32'
              ? 'pip install --no-cache-dir ${ROCM_WHEELS_WIN}'
              : 'pip install --no-cache-dir ${ROCM_WHEELS_LINUX}';
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

    // 7. Pin numpy for Linux ROCm (numpy 2.x incompatible with these wheels)
    {
      when: "{{platform === 'linux'}}",
      method: "shell.run",
      params: {
        message: "pip install numpy==1.26.4",
        path: "app",
        venv: "env"
      }
    },

    // 8. Install Qwen3-TTS and remaining deps
    {
      method: "shell.run",
      params: {
        message: `pip install -e . --no-deps && pip install ${COMMON_DEPS}`,
        path: "app",
        venv: "env"
      }
    },

    // 9. Done
    {
      method: "notify",
      params: {
        message: "Qwen3-TTS installed successfully. Click Start to launch."
      }
    }
  ]
}
