module.exports = {
  daemon: true,
  run: [
    // Read GPU type detected at install time
    {
      method: "fs.read",
      params: { path: "app/gpu_type.txt" }
    },

    // Launch with appropriate env vars per GPU type
    {
      method: "shell.run",
      params: {
        message: "python -u launch_amd.py",
        path: "app",
        venv: "env",
        env: `{{
          const gpu = input.data.trim();
          if (gpu === 'amd_dgpu') {
            // RDNA3/4 — full optimizations including hipBLASLt
            return {
              MIOPEN_FIND_ENFORCE: '3',
              MIOPEN_GEMM_ENFORCE_BACKEND: 'hipblaslt',
              HIPBLASLT_LOG_LEVEL: '0'
            };
          } else if (gpu === 'amd_apu') {
            return {
              MIOPEN_FIND_ENFORCE: '3',
              HIPBLASLT_LOG_LEVEL: '0'
            };
          } else if (gpu === 'amd_rdna2_dgpu') {
            // RDNA2 — hipBLASLt disabled, causes segfaults on gfx103x
            return {
              MIOPEN_FIND_ENFORCE: '3',
              HIPBLASLT_LOG_LEVEL: '0'
            };
          } else {
            return {};
          }
        }}`
      }
    }
  ]
}
