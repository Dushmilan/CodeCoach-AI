#!/usr/bin/env python3
"""
Simple demonstration script for three-language validation system.

This script shows how to use the simple validators for Java, JavaScript, and Python.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.simple_validators import SimpleTestRunner, SimpleResultsDisplay


def demo_two_sum():
    """Demonstrate two-sum problem validation across all three languages."""
    
    print("🎯 Three-Language Validation Demo: Two Sum Problem")
    print("=" * 60)
    
    test_cases = [
        {
            "input": "[2,7,11,15]\n9",
            "expected_output": "[0, 1]",
            "description": "Basic case with target at indices 0 and 1"
        },
        {
            "input": "[3,2,4]\n6",
            "expected_output": "[1, 2]",
            "description": "Non-consecutive indices"
        },
        {
            "input": "[3,3]\n6",
            "expected_output": "[0, 1]",
            "description": "Duplicate values case"
        }
    ]
    
    # Python solution
    python_code = '''
import sys

def twoSum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []

# Read input
nums = eval(sys.stdin.readline().strip())
target = int(sys.stdin.readline().strip())
result = twoSum(nums, target)
print(result)
'''
    
    # JavaScript solution
    javascript_code = '''
const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

let lines = [];
rl.on('line', (line) => {
  lines.push(line);
}).on('close', () => {
  const nums = JSON.parse(lines[0]);
  const target = parseInt(lines[1]);
  
  for (let i = 0; i < nums.length; i++) {
    for (let j = i + 1; j < nums.length; j++) {
      if (nums[i] + nums[j] === target) {
        console.log(JSON.stringify([i, j]));
        process.exit(0);
      }
    }
  }
  console.log(JSON.stringify([]));
});
'''
    
    # Java solution
    java_code = '''
import java.util.Scanner;
import java.util.Arrays;

public class Solution {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        String numsStr = scanner.nextLine();
        int target = scanner.nextInt();
        
        // Parse array
        numsStr = numsStr.replace("[", "").replace("]", "");
        String[] parts = numsStr.split(",");
        int[] nums = new int[parts.length];
        for (int i = 0; i < parts.length; i++) {
            nums[i] = Integer.parseInt(parts[i].trim());
        }
        
        // Find two sum
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[i] + nums[j] == target) {
                    System.out.println(Arrays.toString(new int[]{i, j}));
                    return;
                }
            }
        }
        System.out.println(Arrays.toString(new int[]{}));
    }
}
'''
    
    runner = SimpleTestRunner()
    display = SimpleResultsDisplay()
    
    languages = [
        ("python", python_code),
        ("javascript", javascript_code),
        ("java", java_code)
    ]
    
    for language, code in languages:
        print(f"\n🐍 Testing {language.upper()}:")
        print("-" * 40)
        
        results = runner.run_all_tests(language, code, test_cases)
        print(display.format_results(results))


def demo_error_handling():
    """Demonstrate error handling for common issues."""
    
    print("\n🚨 Error Handling Demo")
    print("=" * 40)
    
    runner = SimpleTestRunner()
    display = SimpleResultsDisplay()
    
    test_case = {
        "input": "[1,2,3]\n5",
        "expected_output": "[0, 2]",
        "description": "Basic test case"
    }
    
    # Python syntax error
    python_error = '''
def twoSum(nums, target)
    return [0, 1]  # Missing colon
'''
    
    print("\n❌ Python Syntax Error:")
    results = runner.run_all_tests('python', python_error, [test_case])
    print(display.format_results(results))
    
    # JavaScript runtime error
    js_error = '''
console.log(undefinedVariable);
'''
    
    print("\n❌ JavaScript Runtime Error:")
    results = runner.run_all_tests('javascript', js_error, [test_case])
    print(display.format_results(results))
    
    # Java compilation error
    java_error = '''
public class Solution {
    public static void main(String[] args) {
        System.out.println([0, 1])  // Invalid array printing
    }
}
'''
    
    print("\n❌ Java Compilation Error:")
    results = runner.run_all_tests('java', java_error, [test_case])
    print(display.format_results(results))


def demo_performance():
    """Demonstrate performance testing."""
    
    print("\n⚡ Performance Demo")
    print("=" * 40)
    
    runner = SimpleTestRunner()
    display = SimpleResultsDisplay()
    
    # Large input test
    large_input = str(list(range(1000))) + "\n999"
    
    test_cases = [
        {
            "input": large_input,
            "expected_output": "[998, 999]",
            "description": "Large array performance test"
        }
    ]
    
    python_code = '''
import sys

def twoSum(nums, target):
    # Optimized solution with hash map
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []

nums = eval(sys.stdin.readline().strip())
target = int(sys.stdin.readline().strip())
result = twoSum(nums, target)
print(result)
'''
    
    print("\n🐍 Python Performance Test:")
    results = runner.run_all_tests('python', python_code, test_cases)
    print(display.format_results(results))


def main():
    """Main demo function."""
    
    print("🚀 CodeCoach AI - Simple Validation Demo")
    print("=" * 50)
    
    # Check if required tools are available
    print("🔍 Checking system requirements...")
    
    tools = {
        'python': 'python',
        'javascript': 'node',
        'java': 'java'
    }
    
    available = []
    for tool, cmd in tools.items():
        try:
            subprocess.run([cmd, '--version'], 
                           capture_output=True, check=True)
            available.append(tool)
            print(f"✅ {tool.upper()} available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool.upper()} not available")
    
    if len(available) < 2:
        print("\n⚠️  Warning: Some tools not available. Demo may be limited.")
    
    # Run demos
    demo_two_sum()
    demo_error_handling()
    demo_performance()
    
    print("\n🎉 Demo completed successfully!")
    print("\nNext steps:")
    print("1. Run tests: pytest tests/test_simple_validators.py -v")
    print("2. Start server: python -m backend.app.main")
    print("3. Test API: curl -X POST http://localhost:8000/api/validate/validate")


if __name__ == "__main__":
    main()