from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import logging
import httpx
from app.services.nim_service import NIMService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api-key-status")
async def check_api_key_status() -> Dict[str, Any]:
    """
    Debug endpoint to check NVIDIA API key configuration and validity.
    
    Returns detailed information about the API key setup and basic connectivity test.
    """
    result = {
        "api_key_present": False,
        "api_key_length": 0,
        "api_key_format_valid": False,
        "environment": os.getenv("ENVIRONMENT", "production"),
        "environment_variables": {},
        "api_test_result": None,
        "error": None
    }
    
    try:
        # Check environment variables
        nvidia_vars = {}
        for key, value in os.environ.items():
            if 'nvidia' in key.lower() or 'key' in key.lower():
                nvidia_vars[key] = '***' + value[-4:] if len(value) >= 4 else '***'
        
        result["environment_variables"] = nvidia_vars
        
        # Check API key
        api_key = os.getenv("NVIDIA_API_KEY")
        if api_key:
            result["api_key_present"] = True
            result["api_key_length"] = len(api_key)
            
            # Basic format validation (NVIDIA keys typically start with 'nvapi-')
            if api_key.startswith('nvapi-') and len(api_key) > 10:
                result["api_key_format_valid"] = True
            
            # Test API connectivity
            try:
                service = NIMService(api_key=api_key)
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                # Make a simple test request to verify key validity
                test_payload = {
                    "model": "nvidia/llama-3.1-nemotron-70b-instruct",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                    "stream": False
                }
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        headers=headers,
                        json=test_payload
                    )
                    
                    if response.status_code == 200:
                        result["api_test_result"] = "success"
                    elif response.status_code == 401:
                        result["api_test_result"] = "invalid_key"
                        result["error"] = "Invalid API key (401 Unauthorized)"
                    else:
                        result["api_test_result"] = "error"
                        result["error"] = f"API returned status {response.status_code}"
                        
            except Exception as e:
                result["api_test_result"] = "error"
                result["error"] = str(e)
        else:
            result["error"] = "NVIDIA_API_KEY environment variable not set"
            
    except Exception as e:
        result["error"] = f"Unexpected error during API key check: {str(e)}"
        logger.error(f"Error in debug endpoint: {e}")
    
    return result

@router.get("/environment")
async def get_environment_info() -> Dict[str, Any]:
    """
    Debug endpoint to show relevant environment information.
    """
    return {
        "environment": os.getenv("ENVIRONMENT", "production"),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "working_directory": os.getcwd(),
        "nvidia_api_key_present": bool(os.getenv("NVIDIA_API_KEY")),
        "all_nvidia_vars": {
            k: v for k, v in os.environ.items() 
            if 'nvidia' in k.lower() or 'key' in k.lower()
        }
    }

@router.get("/test-connection")
async def test_nvidia_connection() -> Dict[str, Any]:
    """
    Test the actual connection to NVIDIA NIM API.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "NVIDIA_API_KEY not configured"
        }
    
    try:
        service = NIMService(api_key=api_key)
        # Test with a simple prompt
        async for chunk in service.get_coaching_response(
            problem="Test problem",
            code="print('hello')",
            language="python",
            message="test",
            mode="hint",
            difficulty="easy"
        ):
            return {
                "success": True,
                "message": "Connection successful",
                "sample_response": chunk[:100] + "..." if len(chunk) > 100 else chunk
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }