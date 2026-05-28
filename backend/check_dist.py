import json

with open('questions/sample_questions.json') as f:
    data = json.load(f)

questions = data['questions']
print(f'Total: {len(questions)}')

cats = {}
diffs = {}
for q in questions:
    cat = q.get('category', 'unknown')
    diff = q.get('difficulty', 'unknown')
    cats[cat] = cats.get(cat, 0) + 1
    diffs[diff] = diffs.get(diff, 0) + 1

print('\nCategories:')
for k, v in sorted(cats.items()):
    print(f'  {k}: {v}')

print('\nDifficulties:')
for k, v in sorted(diffs.items()):
    print(f'  {k}: {v}')
