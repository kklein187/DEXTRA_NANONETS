"""
RunPod Serverless Worker for Document Information Extraction
Lightweight adapter that translates RunPod API requests to Gradio app calls.
"""

import os
import base64
import tempfile
import traceback
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

import runpod
from loguru import logger

# Check CUDA availability
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        GPU_COUNT = torch.cuda.device_count()
        GPU_NAME = torch.cuda.get_device_name(0)
        logger.info(f"✓ CUDA available: {GPU_COUNT} GPU(s) - {GPU_NAME}")
    else:
        logger.warning("⚠️  CUDA not available - will run on CPU (slow)")
except ImportError:
    CUDA_AVAILABLE = False
    logger.warning("⚠️  torch not available - assuming CPU mode")

# Configuration from environment
GRADIO_PORT: int = int(os.getenv("GRADIO_PORT", "7860"))
GRADIO_URL: str = f"http://localhost:{GRADIO_PORT}"
MODEL_NAME: str = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-VL-3B-Instruct")
VLM_PORT: int = int(os.getenv("VLM_PORT", "8000"))
MAX_MODEL_LEN: int = int(os.getenv("MAX_MODEL_LEN", "15000"))
GPU_MEMORY_UTIL: float = float(os.getenv("GPU_MEMORY_UTIL", "0.98"))
MAX_NUM_IMGS: int = int(os.getenv("MAX_NUM_IMGS", "5"))
MAX_STARTUP_WAIT: int = int(os.getenv("MAX_STARTUP_WAIT", "600"))  # seconds to wait for Gradio startup (10 minutes for model loading)
VLLM_START_TIMEOUT: int = int(os.getenv("VLLM_START_TIMEOUT", "600"))  # vLLM model loading timeout

# Global process handle for Gradio
GRADIO_PROCESS: Optional[subprocess.Popen] = None


def is_gradio_running() -> bool:
    """Check if Gradio app is already running."""
    try:
        response = requests.get(f"{GRADIO_URL}/", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_gradio_process():
    """
    Start the Gradio app as a subprocess.
    This is called if Gradio is not already running (fallback mechanism).
    """
    global GRADIO_PROCESS
    
    logger.info("Starting Gradio app as subprocess...")
    logger.info(f"Model: {MODEL_NAME}")
    logger.info(f"Device: {'GPU' if CUDA_AVAILABLE else 'CPU'}")
    
    cmd = [
        "python", "-m", "docext.app.app",
        "--model_name", f"hosted_vllm/{MODEL_NAME}",
        "--vlm_server_host", "0.0.0.0",
        "--vlm_server_port", str(VLM_PORT),
        "--server_port", str(GRADIO_PORT),
        "--max_model_len", str(MAX_MODEL_LEN),
        "--max_num_imgs", str(MAX_NUM_IMGS),
        "--vllm_start_timeout", str(VLLM_START_TIMEOUT),
    ]
    
    # Only add GPU-specific parameters if CUDA is available
    if CUDA_AVAILABLE:
        cmd.extend([
            "--gpu_memory_utilization", str(GPU_MEMORY_UTIL),
        ])
    else:
        logger.warning("CPU mode: GPU parameters skipped")
    
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        GRADIO_PROCESS = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        logger.info(f"Gradio process started with PID: {GRADIO_PROCESS.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to start Gradio process: {str(e)}")
        return False


def wait_for_gradio():
    """
    Wait for Gradio app to be ready.
    First checks if already running (started by start_services.sh).
    If not, attempts to start it as a subprocess (fallback).
    Returns True if ready, raises RuntimeError if unable to start.
    """
    global GRADIO_PROCESS
    
    # Check if already running
    if is_gradio_running():
        logger.info("✓ Gradio app is already running!")
        return True
    
    logger.warning("Gradio app not detected.")
    logger.info("Attempting to start Gradio app...")
    
    # Try to start Gradio as subprocess
    if not start_gradio_process():
        raise RuntimeError("Failed to start Gradio process")
    
    # Wait for Gradio to become ready
    logger.info(f"Waiting for Gradio to start (timeout: {MAX_STARTUP_WAIT}s)...")
    logger.info("This can take 5-10 minutes for model loading...")
    
    max_retries = MAX_STARTUP_WAIT // 5
    
    for i in range(max_retries):
        # Check if process died
        if GRADIO_PROCESS and GRADIO_PROCESS.poll() is not None:
            # Process exited unexpectedly
            stdout, stderr = GRADIO_PROCESS.communicate(timeout=1)
            logger.error("Gradio process exited unexpectedly!")
            logger.error(f"Exit code: {GRADIO_PROCESS.returncode}")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            raise RuntimeError(
                f"Gradio process died during startup (exit code: {GRADIO_PROCESS.returncode})"
            )
        
        # Check if Gradio is responding
        try:
            response = requests.get(f"{GRADIO_URL}/", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Gradio app is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(5)
        if i % 6 == 0:  # Log every 30 seconds
            logger.info(f"Still waiting for Gradio... ({i*5}s/{MAX_STARTUP_WAIT}s)")
    
    raise RuntimeError(
        f"Gradio app not ready after {MAX_STARTUP_WAIT}s. "
        "Check logs for errors."
    )


def decode_base64_files(files_data: List[Dict[str, str]]) -> List[str]:
    """
    Decode base64-encoded files and save them to temporary locations.
    
    Args:
        files_data: List of dicts with 'filename' and 'data' (base64 encoded)
        
    Returns:
        List of temporary file paths
    """
    temp_paths = []
    
    for file_info in files_data:
        try:
            filename = file_info.get("filename", "document")
            base64_data = file_info.get("data", "")
            
            # Remove data URI prefix if present
            if "base64," in base64_data:
                base64_data = base64_data.split("base64,")[1]
            
            # Decode base64
            file_bytes = base64.b64decode(base64_data)
            
            # Determine file extension
            ext = Path(filename).suffix if "." in filename else ".pdf"
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=ext,
                mode='wb'
            )
            temp_file.write(file_bytes)
            temp_file.close()
            
            temp_paths.append(temp_file.name)
            logger.info(f"Saved temporary file: {temp_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to decode file {file_info.get('filename', 'unknown')}: {str(e)}")
            raise
    
    return temp_paths


def cleanup_temp_files(file_paths: List[str]):
    """Remove temporary files after processing."""
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                # Also remove any converted image files
                base_path = path.rsplit('.', 1)[0]
                import glob
                for img_file in glob.glob(f"{base_path}_*.jpg"):
                    os.remove(img_file)
        except Exception as e:
            logger.warning(f"Failed to cleanup file {path}: {str(e)}")


def validate_input(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and parse the input payload.
    
    Expected payload structure:
    {
        "files": [
            {"filename": "doc.pdf", "data": "base64_encoded_data"},
            ...
        ],
        "fields": [
            {"name": "invoice_number", "description": "The invoice number"},
            {"name": "invoice_date", "description": "Date of invoice"},
            ...
        ],
        "tables": [
            {"name": "line_items", "description": "Table of line items"},
            ...
        ],
        "max_img_size": 1024,  # Optional, default 1024
        "model_name": "hosted_vllm/Qwen/Qwen2.5-VL-3B-Instruct"  # Optional
    }
    
    Returns:
        Validated and processed input dictionary
    """
    errors = []
    
    # Validate files
    if "files" not in job_input:
        errors.append("Missing required field: 'files'")
    elif not isinstance(job_input["files"], list):
        errors.append("'files' must be a list")
    elif len(job_input["files"]) == 0:
        errors.append("'files' list cannot be empty")
    
    # Validate fields (optional but at least one of fields/tables required)
    fields = job_input.get("fields", [])
    tables = job_input.get("tables", [])
    
    if not isinstance(fields, list):
        errors.append("'fields' must be a list")
    if not isinstance(tables, list):
        errors.append("'tables' must be a list")
    
    if len(fields) == 0 and len(tables) == 0:
        errors.append("At least one field or table must be specified")
    
    # Validate field structure
    for i, field in enumerate(fields):
        if not isinstance(field, dict):
            errors.append(f"Field at index {i} must be a dictionary")
        elif "name" not in field:
            errors.append(f"Field at index {i} missing required 'name' property")
    
    # Validate table structure
    for i, table in enumerate(tables):
        if not isinstance(table, dict):
            errors.append(f"Table at index {i} must be a dictionary")
        elif "name" not in table:
            errors.append(f"Table at index {i} missing required 'name' property")
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Set defaults
    return {
        "files": job_input["files"],
        "fields": fields,
        "tables": tables,
        "max_img_size": job_input.get("max_img_size", 1024),
        "model_name": job_input.get("model_name", f"hosted_vllm/{MODEL_NAME}"),
    }


def dataframe_to_custom_dict(data: List[Dict]) -> dict:
    """
    Convert list of field/table dicts to Gradio DataFrame format.
    
    Format expected by Gradio API:
    {
        "headers": ["name", "type", "description"],
        "data": [["invoice_number", "field", "Invoice number"], ...],
        "metadata": None
    }
    """
    if not data:
        return {"headers": ["name", "type", "description"], "data": [], "metadata": None}
    
    headers = ["name", "type", "description"]
    rows = []
    
    for item in data:
        rows.append([
            item.get("name", ""),
            item.get("type", "field"),
            item.get("description", "")
        ])
    
    return {
        "headers": headers,
        "data": rows,
        "metadata": None
    }


def dict_to_dataframe(d: dict) -> List[Dict]:
    """Convert Gradio DataFrame dict format back to list of dicts."""
    if not d or not d.get("data"):
        return []
    
    headers = d.get("headers", [])
    data = d.get("data", [])
    
    result = []
    for row in data:
        result.append(dict(zip(headers, row)))
    
    return result


def call_gradio_api(files: List[str], fields: List[Dict], tables: List[Dict], max_img_size: int) -> tuple:
    """
    Call the Gradio app's API endpoint to perform extraction.
    Following the official docext API format.
    
    Args:
        files: List of file paths
        fields: List of field definitions
        tables: List of table definitions
        max_img_size: Maximum image size
        
    Returns:
        Tuple of (fields_list, tables_list)
    """
    try:
        from gradio_client import Client, handle_file
        
        # Create Gradio client
        client = Client(GRADIO_URL, auth=("admin", "admin"))
        
        # Convert files to Gradio file format
        file_inputs = [handle_file(filepath) for filepath in files]
        
        # Combine fields and tables into the format expected by Gradio
        fields_and_tables_data = []
        for field in fields:
            fields_and_tables_data.append({
                "name": field["name"],
                "type": "field",
                "description": field.get("description", "")
            })
        
        for table in tables:
            fields_and_tables_data.append({
                "name": table["name"],
                "type": "table",
                "description": table.get("description", "")
            })
        
        # Convert to Gradio DataFrame format
        fields_and_tables_dict = dataframe_to_custom_dict(fields_and_tables_data)
        
        logger.info(f"Calling Gradio API with {len(file_inputs)} files and {len(fields_and_tables_data)} fields/tables")
        
        # Call the Gradio API endpoint using the official format
        result = client.predict(
            file_inputs=file_inputs,
            model_name=f"hosted_vllm/{MODEL_NAME}",
            fields_and_tables=fields_and_tables_dict,
            api_name="/extract_information"
        )
        
        # Parse results - Gradio returns (fields_dict, tables_dict)
        fields_dict, tables_dict = result
        
        # Convert back from DataFrame format to list of dicts
        fields_list = dict_to_dataframe(fields_dict)
        tables_list = dict_to_dataframe(tables_dict)
        
        logger.info(f"Extraction complete: {len(fields_list)} field results, {len(tables_list)} table results")
        
        return fields_list, tables_list
        
    except Exception as e:
        logger.error(f"Gradio API call failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler function - translates RunPod requests to Gradio API calls.
    
    Args:
        job: RunPod job dictionary containing 'input' key with payload
        
    Returns:
        Dictionary with extraction results or error information
    """
    job_input = job.get("input", {})
    temp_files = []
    
    try:
        logger.info(f"Received job with input keys: {list(job_input.keys())}")
        
        # Validate input
        validated_input = validate_input(job_input)
        
        # Decode and save files temporarily
        temp_files = decode_base64_files(validated_input["files"])
        logger.info(f"Decoded {len(temp_files)} files")
        
        # Call Gradio API
        logger.info(f"Calling Gradio API for extraction...")
        fields_df, tables_df = call_gradio_api(
            files=temp_files,
            fields=validated_input["fields"],
            tables=validated_input["tables"],
            max_img_size=validated_input["max_img_size"]
        )
        
        # Convert results to JSON format
        fields_result = fields_df if isinstance(fields_df, list) else []
        tables_result = tables_df if isinstance(tables_df, list) else []
        
        logger.info(f"Extraction completed: {len(fields_result)} fields, {len(tables_result)} tables")
        
        # Return successful result
        return {
            "success": True,
            "fields": fields_result,
            "tables": tables_result,
            "metadata": {
                "num_documents": len(temp_files),
                "num_fields": len(validated_input["fields"]),
                "num_tables": len(validated_input["tables"]),
                "model_used": validated_input["model_name"],
            }
        }
        
    except ValueError as e:
        # Validation error
        logger.error(f"Validation error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "validation_error"
        }
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Extraction failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "error_type": "processing_error",
            "traceback": traceback.format_exc()
        }
        
    finally:
        # Always cleanup temporary files
        if temp_files:
            cleanup_temp_files(temp_files)
            logger.info("Cleaned up temporary files")


if __name__ == "__main__":
    logger.info("Starting RunPod serverless worker for document extraction")
    
    # Wait for Gradio app to be ready (should be started by start_services.sh)
    wait_for_gradio()
    
    # Start the serverless handler
    logger.info("Starting RunPod serverless handler")
    runpod.serverless.start({
        "handler": handler
    })
