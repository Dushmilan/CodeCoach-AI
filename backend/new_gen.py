import os, sys, json, time, httpx, re

api_key = os.getenv('NVIDIA_API_KEY')

# All 14 DSA topics
TOPICS = [
    "Arrays & Hashing", "Two Pointers", "Sliding Window", "Stack",
    "Binary Search", "Linked List", "Trees", "Tries",
    "Heap / Priority Queue", "Backtracking", "Graphs",
    "Dynamic Programming", "Greedy", "Intervals",
]

VALID_CATEGORIES = set(TOPICS)

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
        
        # Ensure category is valid
        if q.get("category") not in VALID_CATEGORIES:
            continue
        
        # Ensure difficulty is lowercase
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
        
        # Ensure starter code
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

Requirements:
- title: descriptive string
- difficulty: "{difficulty}" (lowercase)
- category: "{topic}" (MUST match exactly)
- description: 2-3 paragraphs explaining the problem
- examples: array of 2 objects with input/output/explanation
- test_cases: array of EXACTLY 12 objects with input/expected_output/description/hidden
  - 3 edge cases
  - 3 standard cases  
  - 6 hidden validation cases (marked "hidden": true)
- starter: object with python/javascript/java function signatures
- hints: array of 3 progressive hint strings
- solution: detailed explanation string
- time_complexity: string like "O(n)"
- space_complexity: string like "O(1)"
- constraints: array of 4-6 constraint strings

Return ONLY the JSON object. Do not use escape characters in strings."""
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    
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
                # Filter for 12 test cases
                valid = [q for q in questions if len(q.get("test_cases", [])) >= 12]
                if valid:
                    return valid[:1]
        except Exception as e:
            continue
    
    return []

# Start fresh with only valid questions
output_file = 'questions/sample_questions.json'

print(f'Generating new DSA questions for all 14 topics')

all_questions = []
for i, topic in enumerate(TOPICS):
    for difficulty in ['easy', 'medium']:
        print(f'[{i+1}/14] {difficulty} for {topic}...', end=' ', flush=True)
        questions = generate_question(topic, difficulty)
        
        for q in questions:
            # Deduplicate by ID
            qid = q['id']
            existing_ids = {x['id'] for x in all_questions}
            if qid in existing_ids:
                counter = 2
                while f"{qid}-{counter}" in existing_ids:
                    counter += 1
                q['id'] = f"{qid}-{counter}"
            all_questions.append(q)
        
        print(f'got {len(questions)}')
        
        # Save periodically
        if (i + 1) % 3 == 0:
            with open(output_file, 'w') as f:
                json.dump({"questions": all_questions}, f, indent=2)
            print(f'  Saved checkpoint ({len(all_questions)} total)')
        
        time.sleep(2)

# Final save
with open(output_file, 'w') as f:
    json.dump({"questions": all_questions}, f, indent=2)

print(f'\nDone! Generated {len(all_questions)} questions')
