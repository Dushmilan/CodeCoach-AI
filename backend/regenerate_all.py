import os, sys, json, time, httpx, re

api_key = os.getenv('NVIDIA_API_KEY')

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
    
    # Fix common JSON issues
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
        
        # Validate category
        if q.get("category") not in VALID_CATEGORIES:
            continue
        
        # Normalize difficulty
        if q.get("difficulty"):
            q["difficulty"] = q["difficulty"].lower()
        
        # Ensure all required fields
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
                "python": f"def {name.replace('-', '_')}(nums):\n    pass",
                "javascript": f"function {name.replace('-', '_')}(nums) {{}}",
                "java": f"class Solution {{\n    public int[] {name.replace('-', '_')}(int[] nums) {{\n        return new int[]{{}};\n    }}\n}}"
            }
        
        q["id"] = slugify(q["title"])
        validated.append(q)
    
    return validated

def validate_question(q):
    """Validate question meets requirements. Returns error or None."""
    if not q.get("title") or len(q["title"]) < 3:
        return "Title too short"
    if not q.get("description") or len(q["description"]) < 100:
        return f"Description too short ({len(q.get('description', ''))} chars)"
    if q.get("difficulty") not in ("easy", "medium", "hard"):
        return f"Invalid difficulty: {q.get('difficulty')}"
    if q.get("category") not in VALID_CATEGORIES:
        return f"Invalid category: {q.get('category')}"
    
    tcs = q.get("test_cases", [])
    if len(tcs) != 12:
        return f"Expected 12 test cases, got {len(tcs)}"
    
    hidden_count = sum(1 for tc in tcs if tc.get("hidden"))
    if hidden_count < 4:
        return f"Expected at least 4 hidden test cases, got {hidden_count}"
    
    if not isinstance(q.get("starter"), dict):
        return "Missing starter object"
    for lang in ("python", "javascript", "java"):
        if lang not in q["starter"]:
            return f"Missing starter for {lang}"
    
    if not q.get("solution"):
        return "Missing solution"
    if not q.get("time_complexity"):
        return "Missing time_complexity"
    if not q.get("space_complexity"):
        return "Missing space_complexity"
    if not q.get("constraints") or len(q["constraints"]) < 3:
        return f"Only {len(q.get('constraints', []))} constraints"
    
    return None

def generate_question(topic, difficulty, retry=0):
    prompt = f"""Generate exactly 1 coding question about "{topic}" at "{difficulty}" difficulty.

REQUIRED JSON FORMAT:
{{
  "title": "descriptive problem name",
  "difficulty": "{difficulty}",
  "category": "{topic}",
  "company_tags": ["Google", "Amazon"],
  "description": "Detailed problem statement with input/output format, constraints, and edge cases. Must be at least 100 characters.",
  "examples": [
    {{"input": "example input", "output": "example output", "explanation": "step by step"}}
  ],
  "test_cases": [
    {{"input": "test input", "expected_output": "expected output", "description": "what this tests", "hidden": false}},
    ... (EXACTLY 12 test cases: 3 edge, 3 standard, 6 hidden with hidden:true)
  ],
  "starter": {{
    "python": "def solution(nums):\\n    pass",
    "javascript": "function solution(nums) {{\\n    \\n}}",
    "java": "class Solution {{\\n    public int[] solution(int[] nums) {{\\n        return new int[]{{}};\\n    }}\\n}}"
  }},
  "hints": ["hint 1", "hint 2", "hint 3"],
  "solution": "Detailed explanation of the optimal approach",
  "time_complexity": "O(n)",
  "space_complexity": "O(1)",
  "constraints": ["constraint 1", "constraint 2", "constraint 3", "constraint 4"]
}}

CRITICAL RULES:
1. category MUST be exactly "{topic}"
2. difficulty MUST be exactly "{difficulty}"
3. EXACTLY 12 test cases (no more, no less)
4. At least 6 test cases must have "hidden": true
5. Description must be 100+ characters
6. Return ONLY the JSON object"""
    
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    
    models = ['meta/llama-3.3-70b-instruct', 'meta/llama-3.1-70b-instruct']
    
    for model in models:
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are a coding question generator. Return ONLY valid JSON.'},
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
                if questions:
                    return questions[0]
        except Exception as e:
            if retry < 2:
                time.sleep(5)
                return generate_question(topic, difficulty, retry + 1)
    
    return None

def main():
    output_file = 'questions/sample_questions.json'
    
    # Start fresh
    all_questions = []
    existing_ids = set()
    
    print(f"Generating questions for all {len(TOPICS)} DSA topics")
    print("=" * 60)
    
    total_generated = 0
    total_failed = 0
    
    for i, topic in enumerate(TOPICS):
        for difficulty in ['easy', 'medium']:
            print(f"[{i+1}/14] {difficulty} {topic}...", end=' ', flush=True)
            
            q = generate_question(topic, difficulty)
            
            if q:
                # Ensure unique ID
                qid = q['id']
                if qid in existing_ids:
                    counter = 2
                    while f"{qid}-{counter}" in existing_ids:
                        counter += 1
                    q['id'] = f"{qid}-{counter}"
                
                existing_ids.add(q['id'])
                all_questions.append(q)
                total_generated += 1
                print(f"OK ({q['id']})")
            else:
                total_failed += 1
                print("FAILED")
            
            time.sleep(2)
        
        # Save checkpoint every 3 topics
        if (i + 1) % 3 == 0:
            with open(output_file, 'w') as f:
                json.dump({"questions": all_questions}, f, indent=2)
            print(f"  Checkpoint: {len(all_questions)} questions saved")
    
    # Final save
    with open(output_file, 'w') as f:
        json.dump({"questions": all_questions}, f, indent=2)
    
    print("=" * 60)
    print(f"Generated: {total_generated} | Failed: {total_failed}")
    print(f"Total questions: {len(all_questions)}")
    
    # Show distribution
    cats = {}
    diffs = {}
    for q in all_questions:
        cats[q['category']] = cats.get(q['category'], 0) + 1
        diffs[q['difficulty']] = diffs.get(q['difficulty'], 0) + 1
    
    print("\nCategory Distribution:")
    for k, v in sorted(cats.items()):
        print(f"  {k}: {v}")
    
    print("\nDifficulty Distribution:")
    for k, v in sorted(diffs.items()):
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
