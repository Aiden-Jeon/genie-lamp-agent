"""Test script to validate Databricks endpoint connectivity.

NOTE: This test makes real LLM API calls which can incur costs.
Set environment variable RUN_LLM_TESTS=true to enable this test.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest

# Add project root to path for standalone execution
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from src.llm.databricks_llm import DatabricksFoundationModelClient


@pytest.mark.llm
@pytest.mark.skipif(
    os.getenv("RUN_LLM_TESTS") != "true",
    reason="Skipped: Makes real LLM API call (costs money). Set RUN_LLM_TESTS=true to run."
)
def test_endpoint():
    """Test the Databricks endpoint connection."""
    print("=" * 80)
    print("🔍 Testing Databricks Endpoint Connection")
    print("=" * 80)
    
    # Get configuration
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    model = os.getenv("LLM_MODEL_NAME", "databricks-gpt-5-2")
    
    print(f"\nConfiguration:")
    print(f"  Host: {host}")
    print(f"  Token: {'*' * 20 if token else 'NOT SET'}")
    print(f"  Model: {model}")
    print()
    
    if not host or not token:
        print("❌ ERROR: DATABRICKS_HOST and DATABRICKS_TOKEN must be set")
        return False
    
    try:
        # Initialize client
        print("📡 Initializing client...")
        client = DatabricksFoundationModelClient(
            model_name=model,
            databricks_host=host,
            databricks_token=token
        )
        print(f"   Endpoint URL: {client.endpoint_url}")
        print()
        
        # Test with a simple prompt
        print("📤 Sending test request...")
        prompt = "Say 'Hello, this is a test' and nothing else."
        
        response = client.generate(
            prompt=prompt,
            max_tokens=50,
            temperature=0.1
        )
        
        print("✅ SUCCESS! Endpoint is reachable")
        print(f"\n📥 Response:")
        print(f"   {response}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to endpoint")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print()
        
        # Print more details for common errors
        if "Connection" in str(e):
            print("💡 Possible causes:")
            print("   - Check if DATABRICKS_HOST is correct")
            print("   - Check network connectivity")
            print("   - Check if you're behind a VPN or firewall")
        elif "401" in str(e) or "403" in str(e):
            print("💡 Possible causes:")
            print("   - Check if DATABRICKS_TOKEN is valid and not expired")
            print("   - Check if the token has proper permissions")
        elif "404" in str(e):
            print("💡 Possible causes:")
            print("   - Check if the model name is correct")
            print("   - Check if the endpoint exists in your workspace")
        elif "timeout" in str(e).lower():
            print("💡 Possible causes:")
            print("   - The endpoint might be slow to respond")
            print("   - Network issues")
            print("   - Try increasing the timeout value")
        
        return False

if __name__ == "__main__":
    success = test_endpoint()
    sys.exit(0 if success else 1)

# Pytest-compatible wrapper
@pytest.mark.llm
@pytest.mark.skipif(
    os.getenv("RUN_LLM_TESTS") != "true",
    reason="Skipped: Makes real LLM API call (costs money). Set RUN_LLM_TESTS=true to run."
)
def test_endpoint_pytest():
    """Pytest wrapper for test_endpoint."""
    result = test_endpoint()
    assert result, "Endpoint test failed"
