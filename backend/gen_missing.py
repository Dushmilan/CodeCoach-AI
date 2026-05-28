import os, sys, json, time, httpx, re

api_key = os.getenv('NVIDIA_API_KEY')

def generate_quick(topic):
    prompt = f"""Return a JSON object for a coding question about {topic}.
Fields: title, difficulty:"easy", category:"{topic}", description (2 paragraphs), examples (2), test_cases (12 with input/expected_output/description/hidden), starter (python/javascript/java), hints (3), solution, time_complexity, space_complexity, constraints (4).
Return ONLY the JSON."""
    
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {
        'model': 'meta/llama-3.1-8b-instruct',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 3000,
        'temperature': 0.7,
    }
    
    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post('https://integrate.api.nvidia.com/v1/chat/completions', headers=headers, json=payload)
        if r.status_code == 200:
            content = r.json()['choices'][0]['message']['content']
            text = content.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            data = json.loads(text)
            if isinstance(data, dict) and 'title' in data:
                return data
    except:
        pass
    return None

# Missing topics
topics = ["Backtracking", "Graphs"]

# Load existing
output_file = 'questions/sample_questions.json'
with open(output_file, 'r') as f:
    existing = json.load(f)
existing_ids = {q['id'] for q in existing.get('questions', [])}

generated = 0
for topic in topics:
    print(f'{topic}...', end=' ', flush=True)
    q = generate_quick(topic)
    if q:
        s = q['title'].lower().strip()
        s = re.sub(r"[^a-z0-9\s-]", "", s)
        s = re.sub(r"[\s-]+", "-", s)
        q['id'] = s
        if q['id'] not in existing_ids:
            existing_ids.add(q['id'])
            existing['questions'].append(q)
            generated += 1
            print('OK')
        else:
            print('duplicate')
    else:
        print('failed')
    time.sleep(1)

with open(output_file, 'w') as f:
    json.dump(existing, f, indent=2)

print(f'\nGenerated {generated}. Total: {len(existing["questions"])}')
