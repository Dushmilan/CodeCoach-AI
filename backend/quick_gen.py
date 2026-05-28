import os, sys, json, time, httpx, re
sys.path.insert(0, os.path.dirname(__file__))

api_key = os.getenv('NVIDIA_API_KEY')

def build_simplified_prompt(topic, difficulty, count):
    return f"""Generate {count} coding interview question(s) about "{topic}" at "{difficulty}" difficulty.

Return a JSON array. Each question must have:
  - title: string
  - difficulty: "{difficulty}"
  - category: "{topic}"
  - description: problem description (2-3 paragraphs)
  - examples: array of 2 examples with input/output/explanation
  - test_cases: array of 6 objects with input/expected_output/description/hidden
  - starter: {{"python": "...", "javascript": "...", "java": "..."}}
  - hints: array of 3 strings
  - solution: string explanation
  - time_complexity: string
  - space_complexity: string
  - constraints: array of 4 strings

Return ONLY the JSON array, no other text."""

def parse_questions(raw):
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    
    try:
        data = json.loads(text)
    except:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
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
            q["starter"] = {
                "python": f"def {q['title'].lower().replace(' ', '_')}():\n    pass",
                "javascript": f"function {q['title'].lower().replace(' ', '_')}() {{}}",
                "java": f"class Solution {{\n    public void {q['title'].lower().replace(' ', '_')}() {{}}\n}}"
            }
        # Slugify ID
        s = q["title"].lower().strip()
        s = re.sub(r"[^a-z0-9\s-]", "", s)
        s = re.sub(r"[\s-]+", "-", s)
        q["id"] = s
        validated.append(q)
    
    return validated

# Generate questions for a topic
topic = "Two Pointers"
difficulty = "easy"
count = 2

prompt = build_simplified_prompt(topic, difficulty, count)
print(f'Generating {count} {difficulty} questions for {topic}...')

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
}
payload = {
    'model': 'meta/llama-3.1-70b-instruct',
    'messages': [
        {'role': 'system', 'content': 'You are a coding question generator. Return ONLY valid JSON.'},
        {'role': 'user', 'content': prompt}
    ],
    'max_tokens': 4000,
    'temperature': 0.7,
    'stream': False,
}

start = time.time()
with httpx.Client(timeout=120.0) as client:
    response = client.post(
        'https://integrate.api.nvidia.com/v1/chat/completions',
        headers=headers,
        json=payload,
    )
elapsed = time.time() - start
print(f'API call: {elapsed:.1f}s, Status: {response.status_code}')

if response.status_code == 200:
    content = response.json()['choices'][0]['message']['content']
    questions = parse_questions(content)
    print(f'Parsed {len(questions)} questions')
    for q in questions:
        tc = len(q.get('test_cases', []))
        print(f'  - {q["title"]} ({tc} test cases)')
    
    # Save to file
    output_file = 'questions/sample_questions.json'
    with open(output_file, 'r') as f:
        existing = json.load(f)
    
    existing_ids = {q['id'] for q in existing.get('questions', [])}
    for q in questions:
        if q['id'] in existing_ids:
            counter = 2
            while f"{q['id']}-{counter}" in existing_ids:
                counter += 1
            q['id'] = f"{q['id']}-{counter}"
        existing_ids.add(q['id'])
        existing['questions'].append(q)
    
    with open(output_file, 'w') as f:
        json.dump(existing, f, indent=2)
    print(f'Saved to {output_file}. Total: {len(existing["questions"])}')
