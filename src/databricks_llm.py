"""Databricks LLM client for calling serving endpoints."""

import json
import os
from typing import Dict, Any, Optional
import requests
from pydantic import ValidationError

from .models import LLMResponse, GenieSpaceConfig


class DatabricksLLMClient:
    """Client for calling Databricks serving endpoints."""
    
    def __init__(
        self,
        endpoint_name: str,
        databricks_host: Optional[str] = None,
        databricks_token: Optional[str] = None
    ):
        """
        Initialize the Databricks LLM client.
        
        Args:
            endpoint_name: Name of the serving endpoint
            databricks_host: Databricks workspace URL (defaults to DATABRICKS_HOST env var)
            databricks_token: Databricks personal access token (defaults to DATABRICKS_TOKEN env var)
        """
        self.endpoint_name = endpoint_name
        self.databricks_host = databricks_host or os.getenv("DATABRICKS_HOST")
        self.databricks_token = databricks_token or os.getenv("DATABRICKS_TOKEN")
        
        if not self.databricks_host:
            raise ValueError("databricks_host must be provided or DATABRICKS_HOST env var must be set")
        if not self.databricks_token:
            raise ValueError("databricks_token must be provided or DATABRICKS_TOKEN env var must be set")
        
        # Clean up host URL
        self.databricks_host = self.databricks_host.rstrip('/')
        if not self.databricks_host.startswith('http'):
            self.databricks_host = f"https://{self.databricks_host}"
        
        self.endpoint_url = f"{self.databricks_host}/serving-endpoints/{self.endpoint_name}/invocations"
        
    def _make_request(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a request to the Databricks serving endpoint.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            **kwargs: Additional parameters to pass to the model
            
        Returns:
            The raw response from the API
        """
        headers = {
            "Authorization": f"Bearer {self.databricks_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        response = requests.post(
            self.endpoint_url,
            headers=headers,
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.1,
        **kwargs
    ) -> str:
        """
        Generate text from the LLM.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            The generated text
        """
        response = self._make_request(prompt, max_tokens, temperature, **kwargs)
        
        # Extract the generated text from the response
        # Note: The exact structure depends on the serving endpoint format
        # Common formats:
        if "choices" in response:
            # OpenAI-style format
            return response["choices"][0]["message"]["content"]
        elif "predictions" in response:
            # MLflow model format
            return response["predictions"][0]
        elif "outputs" in response:
            # Alternative format
            return response["outputs"][0]
        else:
            # Return the whole response as string if format is unknown
            return str(response)
    
    def generate_genie_config(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.1,
        include_reasoning: bool = True,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a Genie space configuration from the LLM.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            include_reasoning: Whether to include reasoning in the response
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object containing the parsed Genie space configuration
            
        Raises:
            ValidationError: If the LLM response doesn't match the expected schema
            json.JSONDecodeError: If the LLM response is not valid JSON
        """
        # Generate the response
        response_text = self.generate(prompt, max_tokens, temperature, **kwargs)
        
        # Try to extract JSON from the response (in case there's extra text)
        response_text = response_text.strip()
        
        # Find JSON object in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError(
                f"No JSON object found in LLM response. Response length: {len(response_text)} chars. "
                f"If using a reasoning model (like GPT-5.2), try increasing max_tokens to 16000+."
            )
        
        json_text = response_text[start_idx:end_idx + 1]
        
        # Parse JSON
        response_data = json.loads(json_text)
        
        # Validate and parse with Pydantic
        if include_reasoning:
            # Response should contain genie_space_config, reasoning, and confidence_score
            return LLMResponse(**response_data)
        else:
            # Response is just the GenieSpaceConfig
            genie_config = GenieSpaceConfig(**response_data)
            return LLMResponse(genie_space_config=genie_config)


class DatabricksFoundationModelClient(DatabricksLLMClient):
    """Client for calling Databricks Foundation Model APIs."""
    
    def __init__(
        self,
        model_name: str = "databricks-gpt-5-2",
        databricks_host: Optional[str] = None,
        databricks_token: Optional[str] = None
    ):
        """
        Initialize client for Databricks Foundation Model API.
        
        Args:
            model_name: Name of the foundation model to use
            databricks_host: Databricks workspace URL
            databricks_token: Databricks personal access token
        """
        # Foundation Model API uses a different endpoint structure
        self.model_name = model_name
        self.databricks_host = databricks_host or os.getenv("DATABRICKS_HOST")
        self.databricks_token = databricks_token or os.getenv("DATABRICKS_TOKEN")
        
        if not self.databricks_host:
            raise ValueError("databricks_host must be provided or DATABRICKS_HOST env var must be set")
        if not self.databricks_token:
            raise ValueError("databricks_token must be provided or DATABRICKS_TOKEN env var must be set")
        
        # Clean up host URL
        self.databricks_host = self.databricks_host.rstrip('/')
        if not self.databricks_host.startswith('http'):
            self.databricks_host = f"https://{self.databricks_host}"
        
        # Foundation Model API endpoint
        self.endpoint_url = f"{self.databricks_host}/serving-endpoints/{self.model_name}/invocations"
        self.endpoint_name = model_name
