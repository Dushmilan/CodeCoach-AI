from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import os
import json
from openai import AsyncOpenAI

app = FastAPI()
client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY", "")
)

@app.post("/api/v1/qa")
async def qa_endpoint(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        
        if content_type.startswith("application/json"):
            body = await request.json()
            question = body.get("question", "")
        else:
            question = (await request.body()).decode()
        
        if not question:
            raise HTTPException(status_code=400, detail="Missing question")
            
        async def generate():
            stream = await client.chat.completions.create(
                model="nvidia/llama-3.1-nemotron-70b-instruct",
                messages=[{"role": "user", "content": question}],
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception:
        raise HTTPException(status_code=400)
