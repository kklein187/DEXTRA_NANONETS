"""
RunPod Serverless Worker for Document Information Extraction
Transforms the Gradio-based docext application into a serverless handler.
"""

import os
import base64
import tempfile
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

import runpod
from loguru import logger
import pandas as pd

# Import core extraction functionality
from docext.core.extract import extract_information
from docext.core.utils import validate_fields_and_tables, validate_file_paths
from docext.core.vllm import VLLMServer

# Global model server - initialized once at startup
MODEL_SERVER: Optional[VLLMServer] = None
MODEL_NAME: str = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-VL-3B-Instruct")
VLM_PORT: int = int(os.getenv("VLM_PORT", "8000"))
MAX_MODEL_LEN: int = int(os.getenv("MAX_MODEL_LEN", "15000"))
GPU_MEMORY_UTIL: float = float(os.getenv("GPU_MEMORY_UTIL", "0.98"))
MAX_NUM_IMGS: int = int(os.getenv("MAX_NUM_IMGS", "5"))


def initialize_model():
    """
    Initialize the VLM model server at startup.
    This runs once when the worker starts, not per request.
    """
    global MODEL_SERVER
    
    try:
        logger.info(f"Initializing VLM server with model: {MODEL_NAME}")
        
        # Set the VLM_MODEL_URL environment variable for the client
        os.environ["VLM_MODEL_URL"] = f"http://0.0.0.0:{VLM_PORT}/v1"
        os.environ["API_KEY"] = os.getenv("API_KEY", "EMPTY")
        
        # Initialize and start the VLM server
        MODEL_SERVER = VLLMServer(
            model_name=f"hosted_vllm/{MODEL_NAME}",
            host="0.0.0.0",
            port=VLM_PORT,
            max_model_len=MAX_MODEL_LEN,
            gpu_memory_utilization=GPU_MEMORY_UTIL,
            max_num_imgs=MAX_NUM_IMGS,
            vllm_start_timeout=300,
        )
        
        MODEL_SERVER.start_server()
        MODEL_SERVER.wait_for_server(timeout=300)
        
        logger.info("VLM server initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize model: {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Model initialization failed: {str(e)}")


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


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod handler function - processes document extraction requests.
    
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
        
        # Prepare fields and tables for extraction
        fields_and_tables = {
            "fields": validated_input["fields"],
            "tables": validated_input["tables"],
        }
        
        # Perform extraction
        logger.info(f"Starting extraction with model: {validated_input['model_name']}")
        fields_df, tables_df = extract_information(
            file_inputs=temp_files,
            model_name=validated_input["model_name"],
            max_img_size=validated_input["max_img_size"],
            fields_and_tables=fields_and_tables,
        )
        
        # Convert DataFrames to JSON-serializable format
        fields_result = []
        if not fields_df.empty:
            fields_result = fields_df.to_dict(orient="records")
        
        tables_result = []
        if not tables_df.empty:
            tables_result = tables_df.to_dict(orient="records")
        
        logger.info(f"Extraction completed: {len(fields_result)} field records, {len(tables_result)} table records")
        
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
    
    # Initialize model once at startup
    initialize_model()
    
    # Start the serverless handler
    logger.info("Starting RunPod serverless handler")
    runpod.serverless.start({
        "handler": handler
    })
