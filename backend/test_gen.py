import os, sys, json, time, httpx

api_key = os.getenv('NVIDIA_API_KEY')

# Test with a simpler prompt
model = 'meta/llama-3.1-70b-instruct'
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
}
payload = {
    'model': model,
    'messages': [
        {'role': 'system', 'content': 'You are a coding question generator. Return ONLY valid JSON.'},
        {'role': 'user', 'content': 'Generate 1 easy coding question about Two Pointers. Return a JSON array with title, difficulty, category, description fields.'}
    ],
    'max_tokens': 2000,
    'temperature': 0.7,
    'stream': False,
}

print(f'Testing with simpler prompt...')
start = time.time()
try:
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            'https://integrate.api.nvidia.com/v1/chat/completions',
            headers=headers,
            json=payload,
        )
    elapsed = time.time() - start
    print(f'Status: {response.status_code}, Time: {elapsed:.1f}s')
    if response.status_code == 200:
        content = response.json()['choices'][0]['message']['content']
        print(f'Response length: {len(content)}')
        print(f'First 500 chars: {content[:500]}')
    else:
        print(f'Error: {response.text[:200]}')
except Exception as e:
    print(f'Exception: {e}')
