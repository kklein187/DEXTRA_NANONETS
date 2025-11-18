"""Ollama service for local field extraction from markdown content."""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class OllamaFieldExtractor:
    """Service for extracting structured data from markdown using local Ollama models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        """Initialize Ollama field extractor.
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name to use (default: llama3.2)
        """
        self.base_url = base_url
        self.model = model
        self._client = None
        self._is_available = None
    
    def _get_client(self):
        """Get Ollama client with lazy loading."""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.base_url)
            except ImportError:
                raise ImportError(
                    "ollama is required for local field extraction. "
                    "Install with: pip install 'docstrange[local-llm]'"
                )
        return self._client
    
    def is_available(self) -> bool:
        """Check if Ollama service is available.
        
        Returns:
            True if Ollama is available and responding
        """
        if self._is_available is not None:
            return self._is_available
        
        try:
            client = self._get_client()
            # Try to list models to test connectivity
            models_response = client.list()
            
            # The official ollama package returns a ListResponse object with models attribute
            available_models = [model.model for model in models_response.models]
            
            if self.model not in available_models and f"{self.model}:latest" not in available_models:
                logger.warning(f"Model {self.model} not found. Available models: {available_models}")
                logger.info(f"Trying to pull model {self.model}...")
                try:
                    client.pull(self.model)
                    logger.info(f"Successfully pulled model {self.model}")
                except Exception as pull_error:
                    logger.error(f"Failed to pull model {self.model}: {pull_error}")
                    self._is_available = False
                    return False
            
            self._is_available = True
            logger.info(f"Ollama service available at {self.base_url} with model {self.model}")
            return True
        except Exception as e:
            self._is_available = False
            logger.warning(f"Ollama service not available: {e}")
            return False
    
    def extract_fields(self, markdown_content: str, specified_fields: List[str]) -> Dict[str, Any]:
        """Extract specified fields from markdown content.
        
        Args:
            markdown_content: The markdown content to extract from
            specified_fields: List of field names to extract
            
        Returns:
            Dictionary with extracted field values
            
        Raises:
            RuntimeError: If Ollama service is not available
            ValueError: If extraction fails
        """
        if not self.is_available():
            raise RuntimeError(
                f"Ollama service not available at {self.base_url}. "
                "Please ensure Ollama is running and the model is available."
            )
        
        # Create prompt for field extraction
        fields_list = ', '.join(specified_fields)
        prompt = f"""Extract the following fields from this document content. Return ONLY a valid JSON object with the extracted values, no additional text or explanation.

Fields to extract: {fields_list}

Document content:
{markdown_content}

Return format: {{"field_name": "extracted_value", ...}}
If a field is not found, use null as the value.

JSON:"""
        
        try:
            client = self._get_client()
            
            # Use the official ollama client
            response = client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "num_predict": 500,  # Limit output length
                    "stop": ["\n\n"],   # Stop at double newline
                }
            )
            
            response_text = response['response']
            
            # Try to find JSON in the response
            try:
                # Try parsing the whole response as JSON first
                extracted_data = json.loads(response_text.strip())
            except json.JSONDecodeError:
                # If that fails, try to find JSON within the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Validate that we got a dictionary
            if not isinstance(extracted_data, dict):
                raise ValueError("Response is not a JSON object")
            
            # Ensure all requested fields are present (with null if not found)
            result_data = {}
            for field in specified_fields:
                result_data[field] = extracted_data.get(field, None)
            
            logger.info(f"Successfully extracted {len(result_data)} fields using Ollama")
            return result_data
            
        except Exception as e:
            logger.error(f"Field extraction failed: {e}")
            raise ValueError(f"Failed to extract fields: {e}")
    
    def extract_with_schema(self, markdown_content: str, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data according to a JSON schema from markdown content.
        
        Args:
            markdown_content: The markdown content to extract from
            json_schema: JSON schema defining the structure and types
            
        Returns:
            Dictionary with extracted data matching the schema
            
        Raises:
            RuntimeError: If Ollama service is not available
            ValueError: If extraction fails
        """
        if not self.is_available():
            raise RuntimeError(
                f"Ollama service not available at {self.base_url}. "
                "Please ensure Ollama is running and the model is available."
            )
        
        # Create prompt for schema-based extraction
        schema_str = json.dumps(json_schema, indent=2)
        prompt = f"""Extract data from this document content according to the provided JSON schema. Return ONLY a valid JSON object that matches the schema structure, no additional text or explanation.

JSON Schema:
{schema_str}

Document content:
{markdown_content}

Return a JSON object that matches the schema exactly. If a field is not found, use null for optional fields or an appropriate default value.

JSON:"""
        
        try:
            client = self._get_client()
            
            # Use the official ollama client
            response = client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "num_predict": 1000,  # Higher limit for complex schemas
                    "stop": ["\n\n"],   # Stop at double newline
                }
            )
            
            response_text = response['response']
            
            # Try to find and parse JSON in the response
            try:
                # Try parsing the whole response as JSON first
                extracted_data = json.loads(response_text.strip())
            except json.JSONDecodeError:
                # If that fails, try to find JSON within the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Validate that we got a dictionary
            if not isinstance(extracted_data, dict):
                raise ValueError("Response is not a JSON object")
            
            logger.info(f"Successfully extracted data with schema using Ollama")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Schema-based extraction failed: {e}")
            raise ValueError(f"Failed to extract with schema: {e}") 

    def extract_document_json(self, markdown_content: str) -> Dict[str, Any]:
        """Extract important fields and their values from document content using Ollama.
        
        Args:
            markdown_content: Raw markdown content to process
            
        Returns:
            Dictionary containing extracted fields and their values with descriptive keys
        """
        if not markdown_content.strip():
            return {"document": {}, "metadata": {"empty_document": True}}
        
        prompt = f"""
Extract all important fields and their values from the following document. Focus on extracting key data points such as:
- Names, dates, amounts, numbers, percentages
- Titles, headings, and important labels
- Contact information (emails, phones, addresses)
- Financial data (prices, totals, costs, revenues)
- Identifiers (IDs, numbers, codes, references)
- Status information and categories
- Key facts and important details
- Table data with column headers and values
- Any structured information that would be valuable for data analysis

Document content:
{markdown_content}

Return ONLY a valid JSON object where keys are the field names and values are the extracted data. Use descriptive field names and preserve data types (numbers as numbers, dates as strings, etc.). Group related fields logically.

JSON:"""

        try:
            client = self._get_client()
            
            # Use the official ollama client
            response = client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.1,  # Low temperature for consistent structure
                    "num_predict": 2000,  # Higher limit for full documents
                    "stop": ["\n\n---", "Human:", "Assistant:"],  # Stop markers
                }
            )
            
            response_text = response['response']
            
            # Try to find and parse JSON in the response
            try:
                # Try parsing the whole response as JSON first
                document_json = json.loads(response_text.strip())
            except json.JSONDecodeError:
                # If that fails, try to find JSON within the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    document_json = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Validate that we got a dictionary
            if not isinstance(document_json, dict):
                raise ValueError("Response is not a JSON object")
            
            # Ensure basic structure exists
            if "document" not in document_json:
                document_json = {"document": document_json}
            
            logger.info(f"Successfully converted document to JSON using Ollama")
            return document_json
            
        except Exception as e:
            logger.error(f"Document JSON conversion failed: {e}")
            raise ValueError(f"Failed to extract document to JSON: {e}") 