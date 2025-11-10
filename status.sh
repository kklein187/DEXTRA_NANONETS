#!/bin/bash
# Quick status checks for RunPod container services

echo "=== Container Status Check ==="
echo ""

# Check if Gradio is responding
echo "🔍 Checking Gradio (port 7860)..."
if curl -s -f http://localhost:7860/ > /dev/null 2>&1; then
    echo "✅ Gradio is UP"
else
    echo "❌ Gradio is DOWN"
fi

# Check if vLLM is responding
echo ""
echo "🔍 Checking vLLM (port 8000)..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ vLLM is UP"
elif curl -s -f http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo "✅ vLLM is UP (models endpoint)"
else
    echo "❌ vLLM is DOWN"
fi

# Check running processes
echo ""
echo "🔍 Checking running processes..."
echo "Python processes:"
ps aux | grep python | grep -v grep | head -5

echo ""
echo "GPU memory usage:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits || echo "nvidia-smi not available"

echo ""
echo "=== Quick Commands ==="
echo "• Check Gradio: curl -s http://localhost:7860/ | head -1"
echo "• Check vLLM: curl -s http://localhost:8000/health"
echo "• View logs: tail -f /var/log/worker.log"
echo "• Restart services: ./start_services.sh"
