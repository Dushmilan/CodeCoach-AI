import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Mock models to match structure
class Course:
    def __init__(self, **data):
        self.id = data['id']
        self.title = data['title']
        self.modules = data['modules']

class Module:
    def __init__(self, **data):
        self.id = data['id']
        self.lessons = data['lessons']

class Lesson:
    def __init__(self, **data):
        self.id = data['id']

def test_load():
    courses_dir = Path("backend/data/courses")
    _courses = {}
    _modules = {}
    _lessons = {}
    
    def _load_file(path, target, model):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        items = data.get("items", [data])
        for item in items:
            obj = model(**item)
            target[obj.id] = obj
            print(f"Loaded {model.__name__}: {obj.id}")

    for root, _, files in os.walk(courses_dir):
        if "course.json" in files:
            _load_file(os.path.join(root, "course.json"), _courses, Course)
        if "modules.json" in files:
            _load_file(os.path.join(root, "modules.json"), _modules, Module)
        if "lessons.json" in files:
            _load_file(os.path.join(root, "lessons.json"), _lessons, Lesson)

    print(f"Total loaded: {len(_courses)} courses, {len(_modules)} modules, {len(_lessons)} lessons")

if __name__ == "__main__":
    test_load()
