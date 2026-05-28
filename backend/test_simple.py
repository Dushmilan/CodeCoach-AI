import os, sys, json, time, httpx, re

api_key = os.getenv('NVIDIA_API_KEY')

def generate_simple(topic, difficulty):
    prompt = f"""Generate 1 coding question about "{topic}" at "{difficulty}".
Return JSON with: title, difficulty, category, description, examples, test_cases, starter, hints, solution, time_complexity, space_complexity, constraints.
Return ONLY the JSON."""
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': 'meta/llama-3.1-70b-instruct',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 2000,
        'temperature': 0.7,
        'stream': False,
    }
    
    print(f'Sending request with 180s timeout...')
    start = time.time()
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                'https://integrate.api.nvidia.com/v1/chat/completions',
                headers=headers,
                json=payload,
            )
        elapsed = time.time() - start
        print(f'Response: {response.status_code} in {elapsed:.1f}s')
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f'Error: {e}')
    return None

result = generate_simple('Two Pointers', 'easy')
if result:
    print(f'Got {len(result)} chars')
    print(result[:500])
