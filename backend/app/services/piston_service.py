import httpx
import json
from typing import Dict, Any, Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class PistonService:
    """Service for executing code via Piston API."""

    def __init__(self):
        self.base_url = "http://localhost:2000/api/v2"
        self.timeout = 30.0
        
        # Supported languages and their versions
        self.languages = {
            "python": {"version": "3.10.0", "aliases": ["py", "python3"]},
            "javascript": {"version": "18.15.0", "aliases": ["js", "node"]},
            "java": {"version": "15.0.2", "aliases": ["java"]},
            "cpp": {"version": "10.2.0", "aliases": ["c++", "cpp"]},
            "c": {"version": "10.2.0", "aliases": ["c"]},
            "go": {"version": "1.16.2", "aliases": ["golang"]},
            "rust": {"version": "1.68.2", "aliases": ["rs", "rust"]},
            "typescript": {"version": "5.0.2", "aliases": ["ts", "typescript"]},
        }
    
    async def execute_code(
        self,
        language: str,
        code: str,
        stdin: str = "",
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute code using Piston API.
        
        Args:
            language: Programming language name
            code: Source code to execute
            stdin: Input to provide to the program
            version: Specific language version (optional)
        
        Returns:
            Execution results including stdout, stderr, and runtime info
        """
        
        if language not in self.languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {language}. Supported: {list(self.languages.keys())}"
            )
        
        lang_config = self.languages[language]
        version_to_use = version or lang_config["version"]
        
        payload = {
            "language": language,
            "version": version_to_use,
            "files": [
                {
                    "name": f"main.{self._get_file_extension(language)}",
                    "content": code
                }
            ],
            "stdin": stdin,
            "args": [],
            "compile_timeout": 10000,
            "run_timeout": 3000,
            "compile_memory_limit": -1,
            "run_memory_limit": -1
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/execute",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Piston API error: {error_text}"
                    )
                
                result = response.json()
                
                # Process and sanitize the response
                return self._process_execution_result(result)
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Code execution timeout"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error during code execution: {str(e)}"
            )
    
    async def get_runtimes(self) -> Dict[str, Any]:
        """
        Get available runtimes from Piston API.
        
        Returns:
            Dictionary of available languages and their versions
        """
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/runtimes")
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Failed to fetch runtimes"
                    )
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching runtimes: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch available runtimes"
            )
    
    def _get_file_extension(self, language: str) -> str:
        """Get file extension for given language."""
        
        extensions = {
            "python": "py",
            "javascript": "js",
            "java": "java",
            "cpp": "cpp",
            "c": "c",
            "go": "go",
            "rust": "rs",
            "typescript": "ts"
        }
        
        return extensions.get(language, "txt")
    
    def _process_execution_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and sanitize execution result."""
        
        # Extract relevant information
        processed = {
            "stdout": result.get("run", {}).get("stdout", ""),
            "stderr": result.get("run", {}).get("stderr", ""),
            "exit_code": result.get("run", {}).get("code", 1),
            "signal": result.get("run", {}).get("signal", None),
            "execution_time": result.get("run", {}).get("stdout", ""),  # Piston returns this in stdout
            "memory_usage": None,  # Piston doesn't provide memory usage
            "language": result.get("language", ""),
            "version": result.get("version", "")
        }
        
        # Clean up stderr to remove compilation warnings
        stderr = processed["stderr"]
        if stderr:
            # Filter out common warnings
            lines = stderr.split('\n')
            filtered_lines = [
                line for line in lines 
                if not any(warning in line.lower() for warning in [
                    "warning", "deprecated", "note:", "#warning"
                ])
            ]
            processed["stderr"] = '\n'.join(filtered_lines).strip()
        
        return processed
    
    def validate_code(self, language: str, code: str) -> Dict[str, Any]:
        """
        Basic code validation before execution.
        
        Args:
            language: Programming language
            code: Source code to validate
        
        Returns:
            Validation result with any warnings or errors
        """
        
        warnings = []
        
        # Basic checks for common issues
        if language == "python":
            if "input(" in code and "import sys" not in code:
                warnings.append("Consider using sys.stdin for better compatibility")
            
            if "print(" in code and not code.strip().endswith(")"):
                warnings.append("Check for unclosed parentheses")
        
        elif language == "javascript":
            if "console.log(" in code and not code.strip().endswith(")"):
                warnings.append("Check for unclosed parentheses")
        
        return {
            "valid": True,
            "warnings": warnings,
            "errors": []
        }