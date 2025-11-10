from __future__ import annotations

import os
import signal
import subprocess
import threading
import time

import requests
import torch
from loguru import logger


class VLLMServer:
    def __init__(
        self,
        model_name: str,
        host: str = "0.0.0.0",
        port: int = 8000,
        max_model_len: int = 15000,
        gpu_memory_utilization: float = 0.98,
        max_num_imgs: int = 5,
        vllm_start_timeout: int = 300,
        dtype: str = "bfloat16",
    ):
        self.host = host
        self.port = port
        self.model_name = model_name
        self.max_model_len = max_model_len
        self.gpu_memory_utilization = gpu_memory_utilization
        self.max_num_imgs = max_num_imgs
        self.server_process = None
        self.url = f"http://{self.host}:{self.port}/v1/models"
        self.vllm_start_timeout = vllm_start_timeout
        self.dtype = dtype
        assert self.dtype in [
            "bfloat16",
            "float16",
        ], "Invalid dtype. Must be 'bfloat16' or 'float16'."

    def start_server(self):
        """Start the vLLM server in a background thread."""
        # Check CUDA availability
        cuda_available = torch.cuda.is_available()
        device = "cuda" if cuda_available else "cpu"
        
        if not cuda_available:
            logger.warning("⚠️  CUDA not available! Running on CPU (will be very slow)")
            logger.warning("For better performance, use a GPU-enabled environment")
        else:
            gpu_count = torch.cuda.device_count()
            logger.info(f"✓ CUDA available with {gpu_count} GPU(s)")
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        
        logger.info(f"Starting vLLM server on {device}...")
        
        # Set environment variables for vLLM/Ray to avoid ZMQ issues
        env = os.environ.copy()
        # Ensure numeric env vars are not set as strings that could break ZMQ
        for key in ['ZMQ_IO_THREADS', 'ZEROMQ_IO_THREADS', 'OMP_NUM_THREADS']:
            env.pop(key, None)
        
        # Command to start the vLLM server
        is_awq = "awq" in self.model_name.lower()
        dtype = self.dtype if not is_awq else "float16"
        command = [
            "vllm",
            "serve",
            self.model_name.replace("hosted_vllm/", ""),
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--dtype",
            dtype,
            "--limit-mm-per-prompt",
            f"image={self.max_num_imgs},video=0",
            "--served-model-name",
            self.model_name.replace("hosted_vllm/", ""),
            "--max-model-len",
            str(self.max_model_len),
            "--enforce-eager",
            "--disable-log-stats",  # disable log stats
        ]
        
        # Add device-specific parameters
        if cuda_available:
            command.extend([
                "--gpu-memory-utilization",
                str(self.gpu_memory_utilization),
            ])
        else:
            # CPU-specific settings
            command.extend([
                "--device", "cpu",
            ])
            logger.warning("Running on CPU - expect very slow inference times (minutes per request)")
        
        if is_awq:
            command.extend(["--quantization", "awq"])

        # Start the server as a subprocess with clean environment
        self.server_process = subprocess.Popen(command, env=env)
        # self.server_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    def wait_for_server(self, timeout: int = 300):
        """Wait until the vLLM server is ready."""
        logger.info("Waiting for vLLM server to be ready...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(self.url)
                if response.status_code == 200:
                    logger.info(
                        f"vLLM server started on {self.host}:{self.port} with PID: {self.server_process.pid if self.server_process else None}",
                    )
                    return True
            except requests.RequestException:
                pass
            time.sleep(2)

        logger.error("Error: vLLM server did not start in time.")
        self.stop_server()
        exit(1)

    def stop_server(self):
        """Stop the vLLM server gracefully."""
        if self.server_process:
            logger.info("Stopping vLLM server...")
            self.server_process.terminate()
            self.server_process.wait()
            logger.info("vLLM server stopped.")

    def run_in_background(self):
        """Run the server in a background thread and wait for readiness."""
        server_thread = threading.Thread(target=self.start_server, daemon=True)
        server_thread.start()
        self.wait_for_server(timeout=self.vllm_start_timeout)
        return server_thread
