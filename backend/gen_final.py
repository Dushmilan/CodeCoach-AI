import os, sys, json, time, httpx, re

api_key = os.getenv('NVIDIA_API_KEY')

# Topics we still need
TOPICS = [
    "Stack", "Tries", "Heap / Priority Queue",
    "Backtracking", "Graphs", "Dynamic Programming", "Greedy", "Intervals",
]

VALID_CATEGORIES = set([
    "Arrays & Hashing", "Two Pointers", "Sliding Window", "Stack",
    "Binary Search", "Linked List", "Trees", "Tries",
    "Heap / Priority Queue", "Backtracking", "Graphs",
    "Dynamic Programming", "Greedy", "Intervals",
])

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
        if q.get("category") not in VALID_CATEGORIES:
            continue
        if q.get("difficulty"):
            q["difficulty"] = q["difficulty"].lower()
        
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

Return a JSON object with:
- title, difficulty: "{difficulty}", category: "{topic}"
- description: 2-3 paragraphs
- examples: 2 objects with input/output/explanation
- test_cases: EXACTLY 12 objects (3 edge, 3 standard, 6 hidden)
- starter: {{"python": "...", "javascript": "...", "java": "..."}}
- hints: 3 strings, solution: string, time_complexity: string, space_complexity: string
- constraints: 4-6 strings

Return ONLY the JSON object."""
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        'model': 'meta/llama-3.3-70b-instruct',
        'messages': [
            {'role': 'system', 'content': 'Return ONLY valid JSON.'},
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 4000,
        'temperature': 0.7,
        'stream': False,
    }
    
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                'https://integrate.api.nvidia.com/v1/chat/completions',
                headers=headers,
                json=payload,
            )
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            questions = parse_questions(content)
            valid = [q for q in questions if len(q.get("test_cases", [])) >= 12]
            return valid[:1] if valid else []
    except:
        pass
    return []

# Load existing
output_file = 'questions/sample_questions.json'
with open(output_file, 'r') as f:
    existing = json.load(f)
existing_ids = {q['id'] for q in existing.get('questions', [])}

print(f'Starting with {len(existing["questions"])} existing questions')

# Generate for remaining topics
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
    
    with open(output_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    time.sleep(2)

print(f'\nDone! Generated {total_generated} questions. Total: {len(existing["questions"])}')
