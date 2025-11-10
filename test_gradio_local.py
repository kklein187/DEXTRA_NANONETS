#!/usr/bin/env python3
"""
Local Test Script for Gradio App
Tests the Gradio app startup and API calls before deploying to RunPod.
"""

import os
import sys
import time
import requests
import subprocess
import signal
from pathlib import Path

# Configuration - matches RunPod worker settings
GRADIO_PORT = 7860
GRADIO_URL = f"http://localhost:{GRADIO_PORT}"
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-VL-3B-Instruct")
VLM_PORT = int(os.getenv("VLM_PORT", "8000"))
MAX_MODEL_LEN = int(os.getenv("MAX_MODEL_LEN", "15000"))
GPU_MEMORY_UTIL = float(os.getenv("GPU_MEMORY_UTIL", "0.98"))
MAX_NUM_IMGS = int(os.getenv("MAX_NUM_IMGS", "5"))

# Global process handle
gradio_process = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n⚠️  Interrupt received, shutting down...")
    cleanup()
    sys.exit(0)


def cleanup():
    """Stop the Gradio process."""
    global gradio_process
    if gradio_process:
        print("🛑 Stopping Gradio process...")
        gradio_process.terminate()
        try:
            gradio_process.wait(timeout=5)
            print("✓ Gradio process stopped")
        except subprocess.TimeoutExpired:
            print("⚠️  Force killing Gradio process...")
            gradio_process.kill()
            gradio_process.wait()


def is_gradio_running():
    """Check if Gradio is responding."""
    try:
        response = requests.get(f"{GRADIO_URL}/", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_gradio():
    """Start the Gradio app."""
    global gradio_process
    
    print("=" * 60)
    print("🚀 Starting Gradio App Locally")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Gradio Port: {GRADIO_PORT}")
    print(f"vLLM Port: {VLM_PORT}")
    print(f"Max Model Length: {MAX_MODEL_LEN}")
    print(f"GPU Memory Utilization: {GPU_MEMORY_UTIL}")
    print(f"Max Images: {MAX_NUM_IMGS}")
    print("=" * 60)
    print()
    
    # Check if already running
    if is_gradio_running():
        print("✓ Gradio app is already running!")
        print(f"  URL: {GRADIO_URL}")
        return True
    
    # Build command
    cmd = [
        "python3", "-m", "docext.app.app",
        "--model_name", f"hosted_vllm/{MODEL_NAME}",
        "--vlm_server_host", "0.0.0.0",
        "--vlm_server_port", str(VLM_PORT),
        "--server_port", str(GRADIO_PORT),
        "--max_model_len", str(MAX_MODEL_LEN),
        "--gpu_memory_utilization", str(GPU_MEMORY_UTIL),
        "--max_num_imgs", str(MAX_NUM_IMGS),
    ]
    
    print("📝 Command:")
    print(f"   {' '.join(cmd)}")
    print()
    
    # Start process
    print("⏳ Starting Gradio process...")
    try:
        gradio_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print(f"✓ Process started with PID: {gradio_process.pid}")
        print()
    except Exception as e:
        print(f"❌ Failed to start process: {e}")
        return False
    
    # Wait for startup with live output
    print("⏳ Waiting for Gradio to become ready...")
    print("   This can take 5-10 minutes for model loading...")
    print("   Press Ctrl+C to cancel")
    print()
    print("-" * 60)
    
    max_wait = 600  # 10 minutes
    start_time = time.time()
    
    # Print process output in real-time
    import threading
    
    def print_output():
        """Print subprocess output in real-time."""
        for line in gradio_process.stdout:
            print(f"[GRADIO] {line}", end='')
    
    output_thread = threading.Thread(target=print_output, daemon=True)
    output_thread.start()
    
    # Check if ready
    while time.time() - start_time < max_wait:
        # Check if process died
        if gradio_process.poll() is not None:
            print()
            print("-" * 60)
            print(f"❌ Gradio process exited unexpectedly (exit code: {gradio_process.returncode})")
            return False
        
        # Check if responding
        if is_gradio_running():
            elapsed = time.time() - start_time
            print()
            print("-" * 60)
            print(f"✓ Gradio app is ready! (took {elapsed:.1f}s)")
            print(f"  URL: {GRADIO_URL}")
            return True
        
        time.sleep(5)
    
    print()
    print("-" * 60)
    print(f"❌ Timeout: Gradio not ready after {max_wait}s")
    return False


def test_gradio_api():
    """Test the Gradio API with a sample request."""
    print()
    print("=" * 60)
    print("🧪 Testing Gradio API")
    print("=" * 60)
    print()
    
    try:
        from gradio_client import Client
        
        print("📡 Connecting to Gradio API...")
        client = Client(GRADIO_URL, auth=("admin", "admin"))
        print("✓ Connected!")
        print()
        
        # Check if test PDF exists
        test_pdf = Path("assets/invoice_test.pdf")
        if not test_pdf.exists():
            print(f"⚠️  Test PDF not found: {test_pdf}")
            print("   Skipping API test")
            return
        
        print(f"📄 Using test file: {test_pdf}")
        print()
        
        # Prepare test data
        from gradio_client import handle_file
        
        fields_and_tables = {
            "headers": ["name", "type", "description"],
            "data": [
                ["invoice_number", "field", "The invoice number"],
                ["invoice_date", "field", "The invoice date"],
                ["total_amount", "field", "Total amount"],
            ],
            "metadata": None
        }
        
        print("🚀 Calling /extract_information endpoint...")
        print("   This may take 10-30 seconds...")
        print()
        
        result = client.predict(
            file_inputs=[handle_file(str(test_pdf))],
            model_name=f"hosted_vllm/{MODEL_NAME}",
            fields_and_tables=fields_and_tables,
            api_name="/extract_information"
        )
        
        print("✓ API call successful!")
        print()
        print("📊 Results:")
        print("-" * 60)
        
        fields_result, tables_result = result
        
        print("Fields:")
        if fields_result and fields_result.get("data"):
            for row in fields_result["data"]:
                print(f"  - {row[0]}: {row[1]}")
        else:
            print("  (none)")
        
        print()
        print("Tables:")
        if tables_result and tables_result.get("data"):
            for row in tables_result["data"]:
                print(f"  - {row[0]}: {row[1]}")
        else:
            print("  (none)")
        
        print("-" * 60)
        print("✅ API test completed successfully!")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function."""
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "Gradio Local Test Script" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    try:
        # Start Gradio
        if not start_gradio():
            print()
            print("❌ Failed to start Gradio app")
            cleanup()
            sys.exit(1)
        
        # Test API
        try:
            test_gradio_api()
        except Exception as e:
            print(f"\n⚠️  API test error: {e}")
        
        # Keep running
        print()
        print("=" * 60)
        print("✓ Gradio app is running")
        print("=" * 60)
        print(f"  URL: {GRADIO_URL}")
        print(f"  PID: {gradio_process.pid}")
        print()
        print("  Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        # Wait indefinitely
        gradio_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
