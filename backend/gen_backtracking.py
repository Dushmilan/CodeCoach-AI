import os, sys, json, time, httpx, re

api_key = os.getenv('NVIDIA_API_KEY')

prompt = """Return a JSON object for a backtracking coding problem.
Example: generate all permutations of a list.

JSON fields: title, difficulty:"easy", category:"Backtracking", description, examples (2), test_cases (12), starter (python/javascript/java), hints (3), solution, time_complexity, space_complexity, constraints (4).
Return ONLY the JSON."""

headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
payload = {
    'model': 'meta/llama-3.1-70b-instruct',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 3000,
    'temperature': 0.7,
}

try:
    with httpx.Client(timeout=180.0) as client:
        r = client.post('https://integrate.api.nvidia.com/v1/chat/completions', headers=headers, json=payload)
    if r.status_code == 200:
        content = r.json()['choices'][0]['message']['content']
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        print(f'Got: {data.get("title", "unknown")}')
        
        # Load and save
        output_file = 'questions/sample_questions.json'
        with open(output_file, 'r') as f:
            existing = json.load(f)
        
        s = data['title'].lower().strip()
        s = re.sub(r"[^a-z0-9\s-]", "", s)
        s = re.sub(r"[\s-]+", "-", s)
        data['id'] = s
        
        existing['questions'].append(data)
        with open(output_file, 'w') as f:
            json.dump(existing, f, indent=2)
        print(f'Saved. Total: {len(existing["questions"])}')
    else:
        print(f'Error: {r.status_code}')
except Exception as e:
    print(f'Error: {e}')
