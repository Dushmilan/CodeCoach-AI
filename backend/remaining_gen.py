import os, sys, json, time, httpx, re

api_key = os.getenv('NVIDIA_API_KEY')

# Topics we still need
TOPICS = [
    "Linked List", "Trees", "Tries", "Heap / Priority Queue",
    "Backtracking", "Graphs", "Dynamic Programming", "Greedy", "Intervals",
]

def slugify(title):
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s)
    return s

def parse_questions(raw):
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    
    # Fix common JSON escape issues
    text = text.replace('\\"', '"')
    text = text.replace('\\n', '\n')
    text = text.replace('\\t', '\t')
    text = text.replace('\\\\', '\\')
    
    try:
        data = json.loads(text)
    except:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except:
                return []
        else:
            return []
    
    if not isinstance(data, list):
        data = [data]
    
    validated = []
    for q in data:
        if not isinstance(q, dict) or "title" not in q:
            continue
        q.setdefault("company_tags", [])
        q.setdefault("examples", [])
        q.setdefault("test_cases", [])
        q.setdefault("hints", [])
        q.setdefault("constraints", [])
        q.setdefault("solution", None)
        q.setdefault("time_complexity", None)
        q.setdefault("space_complexity", None)
        if "starter" not in q or not isinstance(q["starter"], dict):
            name = slugify(q["title"])
            q["starter"] = {
                "python": f"def {name.replace('-', '_')}():\n    pass",
                "javascript": f"function {name.replace('-', '_')}() {{}}",
                "java": f"class Solution {{\n    public void {name.replace('-', '_')}() {{}}\n}}"
            }
        q["id"] = slugify(q["title"])
        validated.append(q)
    
    return validated

def generate_question(topic, difficulty):
    prompt = f"""Generate 1 coding question about "{topic}" at "{difficulty}".
Include: title, difficulty, category (MUST be "{topic}"), description (2+ paragraphs), examples (2), test_cases (6), starter (python/javascript/java), hints (3), solution, time_complexity, space_complexity, constraints (4).
Return ONLY the JSON object. Do not use escape characters in strings."""
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    # Try multiple models in order of preference
    models = [
        'meta/llama-3.3-70b-instruct',
        'meta/llama-3.1-8b-instruct',
        'meta/llama-3.2-3b-instruct',
    ]
    
    for model in models:
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'Return ONLY valid JSON. Do not use escape characters.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 3000,
            'temperature': 0.7,
            'stream': False,
        }
        
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    'https://integrate.api.nvidia.com/v1/chat/completions',
                    headers=headers,
                    json=payload,
                )
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                questions = parse_questions(content)
                if questions:
                    return questions
        except Exception as e:
            continue
    
    return []

# Load existing questions
output_file = 'questions/sample_questions.json'
with open(output_file, 'r') as f:
    existing = json.load(f)
existing_ids = {q['id'] for q in existing.get('questions', [])}

print(f'Starting with {len(existing["questions"])} existing questions')
print(f'Generating for {len(TOPICS)} remaining topics')

# Generate easy questions for remaining topics
total_generated = 0
for i, topic in enumerate(TOPICS):
    print(f'[{i+1}/{len(TOPICS)}] easy for {topic}...', end=' ', flush=True)
    questions = generate_question(topic, 'easy')
    
    for q in questions:
        if q['id'] in existing_ids:
            counter = 2
            while f"{q['id']}-{counter}" in existing_ids:
                counter += 1
            q['id'] = f"{q['id']}-{counter}"
        existing_ids.add(q['id'])
        existing['questions'].append(q)
        total_generated += 1
    
    print(f'got {len(questions)}')
    
    # Save after each topic
    with open(output_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    time.sleep(2)  # Longer delay to avoid rate limits

print(f'\nDone! Generated {total_generated} questions. Total: {len(existing["questions"])}')
