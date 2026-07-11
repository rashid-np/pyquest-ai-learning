"""
Interview Mode Route — PyQuest
================================
Generates LeetCode-style Python interview questions and evaluates solutions
using the existing Groq LLM. All calls go through the backend (not browser).
"""

from flask import Blueprint, request
from services.agents import _call_llm
from utils.responses import success, error
import json, re

interview_bp = Blueprint("interview", __name__, url_prefix="/api/interview")


IQ_CATEGORY_PROMPTS = {
    "arrays":      "Arrays and Lists manipulation in Python",
    "strings":     "String processing and manipulation in Python",
    "hashmaps":    "Hash Maps, Dictionaries and Sets in Python",
    "twopointers": "Two Pointer technique in Python",
    "sliding":     "Sliding Window algorithm in Python",
    "recursion":   "Recursion and Backtracking in Python",
    "dp":          "Dynamic Programming in Python",
    "trees":       "Trees and Graph traversal in Python",
    "sorting":     "Sorting and Binary Search in Python",
    "math":        "Mathematical and Logical problems in Python",
}


def _extract_json_safe(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"No JSON in response: {text[:200]}")


@interview_bp.route("/generate", methods=["POST"])
def generate_question():
    data = request.get_json(silent=True) or {}
    cat_id = data.get("category", "arrays")
    difficulty = data.get("difficulty", "medium").lower()
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"
    cat_label = IQ_CATEGORY_PROMPTS.get(cat_id, "Python programming")

    diff_guide = {
        "easy": "Beginner level — simple, clear problems. Basic data structures, simple loops or conditions. Should be solvable in 5-10 lines of Python.",
        "medium": "Medium LeetCode difficulty — requires algorithmic thinking. Use hash maps, two pointers, or basic dynamic programming.",
        "hard": "Hard LeetCode difficulty — complex algorithms, optimized solutions required. May need advanced DP, graphs, or complex data structures.",
    }

    prompt = f"""You are a technical interview question designer.
Create a {difficulty.upper()} level Python coding interview question about: {cat_label}

Difficulty guidance: {diff_guide[difficulty]}

The question should:
- Be a real algorithmic problem at exactly {difficulty} difficulty
- Have clear input/output examples the student can use to test their solution
- Have a precise function signature

Return ONLY this JSON (no markdown, no extra text):
{{
  "title": "Problem title (5-8 words)",
  "difficulty": "{difficulty.capitalize()}",
  "category": "{cat_label}",
  "description": "Full problem description. What should the function do? Be specific about inputs, outputs, and edge cases. 3-4 sentences.",
  "examples": [
    {{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "nums[0]+nums[1]=9"}},
    {{"input": "nums = [3,2,4], target = 6", "output": "[1,2]", "explanation": "nums[1]+nums[2]=6"}}
  ],
  "constraints": ["1 <= len(arr) <= 10^4", "Values are integers"],
  "function_signature": "def solve(nums, target):\\n    # Write your solution here\\n    pass"
}}"""

    try:
        raw = _call_llm(prompt, max_tokens=900)
        q = _extract_json_safe(raw)
        for f in ["title", "description", "examples", "function_signature"]:
            if f not in q:
                raise ValueError(f"Missing field: {f}")
        q["difficulty"] = difficulty.capitalize()
        return success(data=q, message="Interview question generated.")
    except Exception as e:
        return error(f"Generation failed: {str(e)}", 500)


@interview_bp.route("/evaluate", methods=["POST"])
def evaluate_solution():
    data = request.get_json(silent=True) or {}
    question = data.get("question", {})
    user_code = data.get("user_code", "").strip()

    if not user_code or len(user_code) < 10:
        return error("No solution provided.", 400)
    if not question:
        return error("No question context provided.", 400)

    prompt = f"""You are a senior Python engineer reviewing a candidate's interview solution.

Problem: {question.get('title', '')}
Description: {question.get('description', '')}
Examples: {json.dumps(question.get('examples', []))}

Candidate's solution:
```python
{user_code}
```

Evaluate strictly. Return ONLY this JSON:
{{
  "verdict": "Correct" or "Partially Correct" or "Incorrect",
  "score": integer 0-100,
  "feedback": "2-3 sentences on correctness, approach, edge cases handled",
  "time_complexity": "O(?) with brief reason",
  "space_complexity": "O(?) with brief reason",
  "improvement": "One specific improvement suggestion"
}}"""

    try:
        raw = _call_llm(prompt, max_tokens=400)
        result = _extract_json_safe(raw)
        return success(data=result, message="Evaluation complete.")
    except Exception as e:
        return error(f"Evaluation failed: {str(e)}", 500)


@interview_bp.route("/hint", methods=["POST"])
def get_hint():
    data = request.get_json(silent=True) or {}
    question = data.get("question", {})
    user_code = data.get("user_code", "")

    prompt = f"""You are a Python interview coach giving a hint.
NEVER reveal the full solution. Give guidance only.

Problem: {question.get('title', '')}
Description: {question.get('description', '')}
Student's current attempt:
```python
{user_code or '(no code yet)'}
```

Give exactly 2 encouraging sentences:
1. Point toward the right algorithm or data structure approach
2. Suggest what to think about next

Plain text only. No code."""

    try:
        hint = _call_llm(prompt, max_tokens=120).strip()
        return success(data={"hint": hint}, message="Hint generated.")
    except Exception as e:
        return error(f"Hint failed: {str(e)}", 500)
