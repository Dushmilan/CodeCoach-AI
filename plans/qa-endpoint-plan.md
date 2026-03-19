# Q&A Endpoint Implementation Plan

## Overview
Create a minimal Q&A endpoint that accepts HTTP POST requests with plain-text questions and returns AI-generated responses as plain-text, with no database writes or external connections.

## Architecture
- **Endpoint**: POST `/api/v1/qa`
- **Request Format**: Plain text in body with "question" field
- **Response Format**: Plain text response with AI answer
- **No Database**: All processing in-memory
- **Mock LLM**: Simple echo/placeholder implementation

## Implementation Details

### 1. Request/Response Models
```python
from pydantic import BaseModel

class QARequest(BaseModel):
    question: str

class QAResponse(BaseModel):
    answer: str
```

### 2. Endpoint Structure
- **File**: `backend/app/api/v1/endpoints/qa.py`
- **Router**: New APIRouter for Q&A functionality
- **Method**: POST only (no GET support needed)

### 3. LLM Integration (Mock)
- Simple echo response: "I received your question: [question]"
- Placeholder for future real LLM integration
- No external API calls
- No configuration needed

### 4. Error Handling
- 400 Bad Request: Missing question field
- 422 Unprocessable Entity: Invalid request format
- 500 Internal Server Error: Processing errors

### 5. Testing Strategy
- Unit tests for request validation
- Integration tests for endpoint
- Manual testing with curl/Postman

## File Structure Changes
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── qa.py (NEW)
│   │       └── api.py (MODIFY)
```

## Implementation Steps
1. Create `qa.py` endpoint file
2. Add request/response models
3. Implement mock LLM processing
4. Add router registration
5. Test endpoint
6. Document usage

## Usage Examples
```bash
# Test with curl
curl -X POST http://localhost:8000/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the time complexity of quicksort?"}'

# Expected response
"I received your question: What is the time complexity of quicksort?"