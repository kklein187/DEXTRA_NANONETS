#!/bin/bash
# Startup script for RunPod deployment
# Starts Gradio app in background, then starts RunPod worker

set -e

echo "========================================="
echo "Starting Document Extraction Services"
echo "========================================="

# Configuration from environment variables
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-VL-3B-Instruct}"
VLM_PORT="${VLM_PORT:-8000}"
GRADIO_PORT="${GRADIO_PORT:-7860}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-15000}"
GPU_MEMORY_UTIL="${GPU_MEMORY_UTIL:-0.98}"
MAX_NUM_IMGS="${MAX_NUM_IMGS:-5}"

echo "Configuration:"
echo "  Model: $MODEL_NAME"
echo "  vLLM Port: $VLM_PORT"
echo "  Gradio Port: $GRADIO_PORT"
echo "  Max Model Length: $MAX_MODEL_LEN"
echo "  GPU Memory Utilization: $GPU_MEMORY_UTIL"
echo ""

# Start Gradio app in background
echo "Starting Gradio app with vLLM server..."
python -m docext.app.app \
    --model_name "hosted_vllm/${MODEL_NAME}" \
    --vlm_server_host "0.0.0.0" \
    --vlm_server_port "$VLM_PORT" \
    --server_port "$GRADIO_PORT" \
    --max_model_len "$MAX_MODEL_LEN" \
    --gpu_memory_utilization "$GPU_MEMORY_UTIL" \
    --max_num_imgs "$MAX_NUM_IMGS" \
    > /tmp/gradio.log 2>&1 &

GRADIO_PID=$!
echo "Gradio app started with PID: $GRADIO_PID"
echo "Logs: /tmp/gradio.log"

# Wait for Gradio to be ready
echo ""
echo "Waiting for Gradio app to be ready..."
echo "This may take 5-10 minutes for model loading..."

MAX_WAIT=600  # 10 minutes
ELAPSED=0
GRADIO_URL="http://localhost:${GRADIO_PORT}"

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -s -f "$GRADIO_URL/" > /dev/null 2>&1; then
        echo "✓ Gradio app is ready!"
        break
    fi
    
    # Check if process is still running
    if ! kill -0 $GRADIO_PID 2>/dev/null; then
        echo "✗ Gradio process died during startup!"
        echo "Last 50 lines of log:"
        tail -50 /tmp/gradio.log
        exit 1
    fi
    
    if [ $((ELAPSED % 30)) -eq 0 ]; then
        echo "  Still waiting... (${ELAPSED}s/${MAX_WAIT}s)"
        echo "  Recent log:"
        tail -5 /tmp/gradio.log | sed 's/^/    /'
    fi
    
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "✗ Gradio app did not become ready within ${MAX_WAIT}s"
    echo "Last 50 lines of log:"
    tail -50 /tmp/gradio.log
    exit 1
fi

echo ""
echo "========================================="
echo "Services Ready - Starting RunPod Worker"
echo "========================================="
echo ""

# Start RunPod worker (this blocks)
exec python -u worker.py
