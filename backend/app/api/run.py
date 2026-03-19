from fastapi import APIRouter, HTTPException
from app.models.schemas import CodeExecutionRequest, CodeExecutionResult, Language
from app.services.piston_service import PistonService

router = APIRouter()

# Initialize Piston service
piston_service = PistonService()

@router.post("/", response_model=CodeExecutionResult)
async def execute_code(request: CodeExecutionRequest):
    """
    Execute code using Piston API.
    
    Supports multiple programming languages with safe execution environment.
    """
    
    try:
        result = await piston_service.execute_code(
            language=request.language.value,
            code=request.code,
            stdin=request.stdin,
            version=request.version
        )
        
        return CodeExecutionResult(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing code: {str(e)}"
        )

@router.post("/validate")
async def validate_code(request: CodeExecutionRequest):
    """
    Validate code before execution.
    
    Provides syntax checking and basic validation without full execution.
    """
    
    try:
        validation = piston_service.validate_code(
            language=request.language.value,
            code=request.code
        )
        
        return {
            "valid": validation["valid"],
            "warnings": validation["warnings"],
            "errors": validation["errors"],
            "language": request.language.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating code: {str(e)}"
        )

@router.get("/languages")
async def get_supported_languages():
    """Get supported programming languages and their versions."""
    
    try:
        runtimes = await piston_service.get_runtimes()
        
        # Filter and format the runtimes
        supported_languages = []
        for runtime in runtimes:
            language = runtime.get("language", "")
            if language in [lang.value for lang in Language]:
                supported_languages.append({
                    "language": language,
                    "version": runtime.get("version", ""),
                    "aliases": runtime.get("aliases", []),
                    "runtime": runtime.get("runtime", "")
                })
        
        return {
            "languages": supported_languages,
            "total": len(supported_languages)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching languages: {str(e)}"
        )

@router.get("/runtimes")
async def get_runtimes():
    """Get all available runtimes from Piston API."""
    
    try:
        runtimes = await piston_service.get_runtimes()
        return {"runtimes": runtimes}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching runtimes: {str(e)}"
        )