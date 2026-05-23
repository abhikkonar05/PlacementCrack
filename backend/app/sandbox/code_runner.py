import sys
import subprocess
import tempfile
import os
from typing import Dict, Any

# DSA problem definitions containing metadata, test-harness injection code
PROBLEMS = {
    "two_sum": {
        "title": "Two Sum",
        "difficulty": "Easy",
        "description": (
            "Given an array of integers `nums` and an integer `target`, "
            "return indices of the two numbers such that they add up to `target`.\n\n"
            "You may assume that each input would have exactly one solution, "
            "and you may not use the same element twice.\n\n"
            "**Example:**\n"
            "Input: `nums = [2, 7, 11, 15]`, `target = 9`\n"
            "Output: `[0, 1]`\n"
            "Explanation: Because `nums[0] + nums[1] == 9`, we return `[0, 1]`."
        ),
        "template": "def two_sum(nums: list, target: int) -> list:\n    # Write your code here\n    pass\n",
        "harness": """
# Test Harness
try:
    r1 = two_sum([2, 7, 11, 15], 9)
    assert sorted(r1) == [0, 1], f"Expected [0, 1], got {r1}"
    
    r2 = two_sum([3, 2, 4], 6)
    assert sorted(r2) == [1, 2], f"Expected [1, 2], got {r2}"
    
    r3 = two_sum([3, 3], 6)
    assert sorted(r3) == [0, 1], f"Expected [0, 1], got {r3}"
    
    print("ALL_TESTS_PASSED")
except AssertionError as e:
    print(f"ASSERTION_FAILED: {e}")
except Exception as e:
    print(f"RUN_ERROR: {type(e).__name__}: {str(e)}")
"""
    },
    "longest_substring": {
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "Medium",
        "description": (
            "Given a string `s`, find the length of the longest substring without repeating characters.\n\n"
            "**Example 1:**\n"
            "Input: `s = \"abcabcbb\"`\n"
            "Output: `3`\n"
            "Explanation: The answer is `\"abc\"`, with the length of 3.\n\n"
            "**Example 2:**\n"
            "Input: `s = \"bbbbb\"`\n"
            "Output: `1`\n"
            "Explanation: The answer is `\"b\"`, with the length of 1."
        ),
        "template": "def length_of_longest_substring(s: str) -> int:\n    # Write your code here\n    pass\n",
        "harness": """
# Test Harness
try:
    r1 = length_of_longest_substring("abcabcbb")
    assert r1 == 3, f"Expected 3, got {r1}"
    
    r2 = length_of_longest_substring("bbbbb")
    assert r2 == 1, f"Expected 1, got {r2}"
    
    r3 = length_of_longest_substring("pwwkew")
    assert r3 == 3, f"Expected 3, got {r3}"
    
    r4 = length_of_longest_substring("")
    assert r4 == 0, f"Expected 0, got {r4}"
    
    print("ALL_TESTS_PASSED")
except AssertionError as e:
    print(f"ASSERTION_FAILED: {e}")
except Exception as e:
    print(f"RUN_ERROR: {type(e).__name__}: {str(e)}")
"""
    },
    "trapping_rain_water": {
        "title": "Trapping Rain Water",
        "difficulty": "Hard",
        "description": (
            "Given `n` non-negative integers representing an elevation map where the width of each bar is 1, "
            "compute how much water it can trap after raining.\n\n"
            "**Example 1:**\n"
            "Input: `height = [0,1,0,2,1,0,1,3,2,1,2,1]`\n"
            "Output: `6`\n\n"
            "**Example 2:**\n"
            "Input: `height = [4,2,0,3,2,5]`\n"
            "Output: `9`"
        ),
        "template": "def trap(height: list) -> int:\n    # Write your code here\n    pass\n",
        "harness": """
# Test Harness
try:
    r1 = trap([0,1,0,2,1,0,1,3,2,1,2,1])
    assert r1 == 6, f"Expected 6, got {r1}"
    
    r2 = trap([4,2,0,3,2,5])
    assert r2 == 9, f"Expected 9, got {r2}"
    
    r3 = trap([])
    assert r3 == 0, f"Expected 0, got {r3}"
    
    print("ALL_TESTS_PASSED")
except AssertionError as e:
    print(f"ASSERTION_FAILED: {e}")
except Exception as e:
    print(f"RUN_ERROR: {type(e).__name__}: {str(e)}")
"""
    }
}

def run_code_sandbox(problem_id: str, code: str, language: str) -> Dict[str, Any]:
    """Runs coding submission in a secure python sandbox with timeout controls."""
    if language.lower() != "python":
        return {
            "status": "Error",
            "message": "Only Python language is currently supported in this sandbox.",
            "time_complexity": "N/A",
            "space_complexity": "N/A",
            "feedback": "Please select Python to run your code."
        }
        
    problem = PROBLEMS.get(problem_id)
    if not problem:
        return {
            "status": "Error",
            "message": "Problem not found.",
            "time_complexity": "N/A",
            "space_complexity": "N/A",
            "feedback": ""
        }
        
    # Assemble user code with test harness
    full_script = f"{code}\n\n{problem['harness']}"
    
    # Write to a temporary file with a unique name to prevent concurrent execution conflicts
    import uuid
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"submission_{problem_id}_{uuid.uuid4().hex}.py")
    
    try:
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(full_script)
            
        # Execute script in isolated subprocess
        # Use python executable running the current app
        python_exe = sys.executable
        
        result = subprocess.run(
            [python_exe, temp_file_path],
            capture_output=True,
            text=True,
            timeout=3.0 # Timeout limit for safety
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        # Analyze results
        if result.returncode != 0:
            # Runtime error
            error_message = stderr if stderr else stdout
            # Clean path from error messages to hide internal paths
            clean_error = error_message.replace(temp_file_path, "solution.py")
            return {
                "status": "Error",
                "message": clean_error,
                "time_complexity": "N/A",
                "space_complexity": "N/A",
                "feedback": "Your code encountered runtime exceptions. Review syntax, recursion limits, or index variables."
            }
            
        if "ALL_TESTS_PASSED" in stdout:
            # Pass
            time_complex, space_complex, feedback = generate_complexity_feedback(problem_id, code)
            return {
                "status": "Pass",
                "message": "All test cases passed successfully!",
                "time_complexity": time_complex,
                "space_complexity": space_complex,
                "feedback": feedback
            }
        elif "ASSERTION_FAILED" in stdout:
            assertion_err = [line for line in stdout.splitlines() if "ASSERTION_FAILED" in line][0]
            return {
                "status": "Fail",
                "message": assertion_err.replace("ASSERTION_FAILED: ", ""),
                "time_complexity": "N/A",
                "space_complexity": "N/A",
                "feedback": "Some assertion test cases failed. Make sure your logic handles all edge cases."
            }
        else:
            run_err = [line for line in stdout.splitlines() if "RUN_ERROR" in line]
            err_msg = run_err[0] if run_err else "Unknown evaluation error"
            return {
                "status": "Error",
                "message": err_msg,
                "time_complexity": "N/A",
                "space_complexity": "N/A",
                "feedback": "An unexpected error occurred during execution."
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "Error",
            "message": "Time Limit Exceeded (TLE). Infinite loop or extremely slow execution detected.",
            "time_complexity": "N/A",
            "space_complexity": "N/A",
            "feedback": "Optimize your loops and recursion depth. Make sure your termination conditions are correct."
        }
    except Exception as e:
        return {
            "status": "Error",
            "message": f"Sandbox error: {str(e)}",
            "time_complexity": "N/A",
            "space_complexity": "N/A",
            "feedback": "An unexpected issue occurred within the sandbox runner."
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

def generate_complexity_feedback(problem_id: str, code: str) -> tuple:
    """Estimates time/space complexities of user code and provides constructive suggestions."""
    # Analyze coding style through simple code parser
    # 1. Look for loops to estimate time complexity
    has_double_loop = False
    has_single_loop = False
    
    # Remove comments to avoid fake positive loops
    cleaned_code = "\n".join([line for line in code.splitlines() if not line.strip().startswith("#")])
    
    # Check for nested loops
    loop_count = 0
    lines = cleaned_code.splitlines()
    for i, line in enumerate(lines):
        if "for " in line or "while " in line:
            loop_count += 1
            # Check indentation of subsequent lines to check if they have loops
            indent = len(line) - len(line.lstrip())
            for next_line in lines[i+1:]:
                if next_line.strip() == "":
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= indent:
                    break # Loop block ended
                if ("for " in next_line or "while " in next_line) and next_indent > indent:
                    has_double_loop = True
                    break
            has_single_loop = True
            
    # Check space complexity indicators (lists, dictionaries, sets creations)
    uses_extra_space = False
    if "dict(" in cleaned_code or "{" in cleaned_code or "[]" in cleaned_code or "list(" in cleaned_code or "set(" in cleaned_code:
        # Check if list/map size scales with input
        if "append(" in cleaned_code or "add(" in cleaned_code or "[" in cleaned_code:
            uses_extra_space = True
            
    # Tailor based on problem
    if problem_id == "two_sum":
        if has_double_loop:
            return (
                "O(N²)", "O(1)",
                "Correct! Your solution is O(N²) because of nested loops. You can optimize this to O(N) time complexity using a Hash Map to store seen complements."
            )
        else:
            return (
                "O(N)", "O(N)",
                "Optimal! Your solution utilizes a Hash Map to find the target pair in single-pass O(N) time complexity. Excellent work!"
            )
            
    elif problem_id == "longest_substring":
        if has_double_loop:
            return (
                "O(N²)", "O(N)",
                "Correct! The nested loop sliding window takes O(N²) time. You can optimize this to O(N) time using a sliding window technique with a map of character positions."
            )
        else:
            return (
                "O(N)", "O(N)",
                "Optimal! You solved this using a sliding window algorithm in linear O(N) time. Great work on structuring the pointers!"
            )
            
    elif problem_id == "trapping_rain_water":
        if has_double_loop:
            return (
                "O(N²)", "O(1)",
                "Correct, but sub-optimal. The nested loops to search maximum elements on the left and right takes O(N²). Try optimizing with dynamic programming or the two-pointer technique to achieve O(N) time."
            )
        elif uses_extra_space:
            return (
                "O(N)", "O(N)",
                "Correct! The Dynamic Programming approach using auxiliary arrays for max-left and max-right heights solves the problem in O(N) time with O(N) space. You can reduce space complexity to O(1) using two pointers."
            )
        else:
            return (
                "O(N)", "O(1)",
                "Optimal! You solved it using the O(N) time and O(1) space two-pointer approach. Industry-level code!"
            )
            
    return ("O(N)", "O(N)", "Well done! The solution is correct and handles edge cases.")
