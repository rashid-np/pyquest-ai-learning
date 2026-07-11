"""
AI Agents — PyQuest
====================
Agent 1 → Question Generator   (zero bad questions, code-writing blanks)
Agent 2 → Sandbox Code Analysis (runs code, 2-line explanation)
Agent 3 → LLM Answer Verifier   (primary correctness + alternative check)
Agent 4 → Hint Generator        (costs -10 pts, never reveals answer)
"""

import json
import re
import subprocess
import sys
from flask import current_app


# ─────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────

def _call_llm(prompt: str, max_tokens: int = 1024) -> str:
    from groq import Groq
    api_key = current_app.config.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in config.py")
    model = current_app.config.get("GROQ_MODEL", "llama-3.1-8b-instant")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content


def _extract_json(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"No JSON found:\n{text[:300]}")


FORBIDDEN_CODE = [
    r"\bimport\b", r"\beval\b", r"\bexec\b",
    r"__[a-zA-Z]+__", r"\bopen\b", r"\bos\b",
    r"\bsys\b", r"\bsubprocess\b",
]

def _safety_check(code: str) -> None:
    for p in FORBIDDEN_CODE:
        if re.search(p, code):
            raise ValueError(f"Unsafe pattern: {p}")


def _run_code(code: str, timeout: int = 3) -> tuple:
    """Run code in subprocess. Returns (stdout, stderr, returncode)."""
    code = code.replace(";", "\n")
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout
        )
        return proc.stdout.strip(), proc.stderr.strip(), proc.returncode
    except subprocess.TimeoutExpired:
        return "", "Time limit exceeded", -1
    except Exception as e:
        return "", str(e), -1


# ══════════════════════════════════════════════════════════════
# AGENT 1 — Question Generator
# ══════════════════════════════════════════════════════════════

BLANK_COUNT = {"easy": 1, "medium": 2, "hard": 3}

_DIFF_GUIDE = {
    "easy": """\
EASY — 1 blank. Blank must be a Python expression, method call, or operator.
Student must think about what code to write — not just fill a value.

GOOD examples:
  template: "nums = [3,1,4,1,5]\\nprint(______)"        answer: "len(nums)"
  template: "x = -7\\nprint(______)"                     answer: "abs(x)"
  template: "s = 'hello'\\nprint(s.______)"              answer: "upper()"
  template: "s = 'hello'\\nprint(s.______)"              answer: "capitalize()"
  template: "x = 10\\nif x ______ 0:\\n    print('positive')\\nelse:\\n    print('not')"  answer: ">"
  template: "total = 0\\nfor i in range(5):\\n    total ______ i\\nprint(total)"  answer: "+="
  template: "name = 'alice'\\nprint(name.______)"        answer: "title()"

BAD (just filling a value — student learns nothing):
  template: "x = ______\\nprint(x)"   answer: "42"    ← NEVER DO THIS""",

    "medium": """\
MEDIUM — 2 blanks. Each blank is a meaningful code fragment.

GOOD examples:
  template: "s = 'Hello World'\\nprint(s.______)\\nprint(s.______)"
  answers:  ["upper()", "lower()"]

  template: "total = 0\\nfor i in range(______):\\n    total ______ i\\nprint(total)"
  answers:  ["6", "+="]

  template: "x = 15\\nif x ______ 2 == 0:\\n    print('even')\\nelse:\\n    print(______)"
  answers:  ["%", "'odd'"]

  template: "word = 'python'\\nprint(______)\\nprint(______)"
  answers:  ["len(word)", "word.upper()"]

BAD (just filling values):
  template: "x = ______\\ny = ______\\nprint(x+y)"
  answers:  ["5", "3"]  ← NEVER DO THIS""",

    "hard": """\
HARD — 3 blanks. Each blank is a meaningful code fragment testing real Python knowledge.

GOOD examples:
  template: "words = 'the quick fox'.______\\nresult = ''\\nfor w in words:\\n    result ______ w.______\\nprint(result)"
  answers:  ["split()", "+=", "capitalize() + ' '"]

  template: "s = 'hello world'\\nprint(s.______)\\nprint(s.______)\\nprint(______)"
  answers:  ["upper()", "title()", "len(s)"]

  template: "nums = [3,1,4,1,5,9]\\ntotal = 0\\nfor n in nums:\\n    if n ______ 4:\\n        total ______ n\\nprint(______)\\nprint(total)"
  answers:  [">", "+=", "len(nums)"]

BAD (just filling values):
  template: "a=______\\nb=______\\nc=______\\nprint(a+b+c)"
  answers:  ["1","2","3"]  ← NEVER DO THIS"""
}


def question_generator_agent(topic: str, difficulty: str,
                              past_titles: list = None) -> dict:
    """
    Generates a validated puzzle. Retries up to 4 times.
    Only returns when filled code actually executes correctly.
    """
    past_titles = past_titles or []
    num_blanks  = BLANK_COUNT.get(difficulty.lower(), 1)

    avoid = ""
    if past_titles:
        titles = "\n".join(f"  - {t}" for t in past_titles[-15:])
        avoid  = f"\nALREADY USED — your puzzle must be completely different:\n{titles}\n"

    base_prompt = f"""You are a Python puzzle designer for a beginner learning game.
Create a fill-in-the-blank Python puzzle.

Topic: {topic}
Difficulty: {difficulty}
Number of blanks required: {num_blanks}
{avoid}
{_DIFF_GUIDE.get(difficulty.lower(), _DIFF_GUIDE['easy'])}

TOPIC-SPECIFIC RULES — the puzzle content must directly match the topic:
- If the topic mentions "variable" or "datatype" or "assignment": blanks must involve actual variable names, type names (int/str/float/bool/list), or assignment operators — e.g. blank = "int", blank = "str", blank = "float", blank = "bool"
- If the topic mentions "string": blanks must be string methods like upper(), lower(), replace(), split(), find(), strip()
- If the topic mentions "list": blanks must be list methods like append(), pop(), sort(), reverse(), len()
- If the topic mentions "loop" or "iteration": blanks must be range() calls, loop conditions, or loop operators
- If the topic mentions "function": blanks must be def syntax, return values, or function calls
- If the topic mentions "conditional": blanks must be comparison operators or boolean expressions
- If the topic mentions "dictionary": blanks must be dict methods or key access patterns
- Always use the EXACT subtopic concept in the code — e.g. for "upper() and lower()" topic, use .upper() and .lower() as blanks

ABSOLUTE RULES:
1. template_code must have EXACTLY {num_blanks} blank(s) written as ______
2. correct_answers is a JSON list of exactly {num_blanks} string(s), one per blank in order
3. ALL variables used in the code MUST be defined WITHIN template_code — NEVER use undefined variables
4. Blanks MUST require writing real Python code — not just assigning a plain number or string
5. The filled code MUST run without ANY error AND print output to stdout
6. problem_statement is one clear sentence describing what the code does

MANDATORY SELF-CHECK before writing JSON:
  - Fill each ______ with its correct_answer
  - Does the code run without any error? If NO → redesign completely
  - Does it print something? If NO → add print() and redesign
  - Does each blank require Python knowledge? If NO → redesign
  - Does the blank relate directly to the stated topic? If NO → redesign

Return ONLY this JSON:
{{
  "title": "short descriptive unique title",
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "problem_statement": "one sentence what the code does",
  "template_code": "python code with exactly {num_blanks} ______",
  "correct_answers": {json.dumps(["answer_" + str(i+1) for i in range(num_blanks)])}
}}"""

    last_error = "No attempts made"
    prompt     = base_prompt

    for attempt in range(4):
        try:
            raw  = _call_llm(prompt, max_tokens=1200)
            data = _extract_json(raw)

            for f in ["title", "topic", "difficulty", "problem_statement",
                      "template_code", "correct_answers"]:
                if f not in data:
                    raise ValueError(f"Missing field: {f}")

            data["template_code"] = re.sub(r"_{3,}", "______", data["template_code"])

            if not isinstance(data["correct_answers"], list):
                data["correct_answers"] = [str(data["correct_answers"])]

            actual_blanks = data["template_code"].count("______")
            if actual_blanks != num_blanks:
                raise ValueError(
                    f"Need {num_blanks} blank(s), got {actual_blanks}"
                )
            if len(data["correct_answers"]) != num_blanks:
                raise ValueError(
                    f"Need {num_blanks} answer(s), got {len(data['correct_answers'])}"
                )

            _safety_check(data["template_code"])
            for ans in data["correct_answers"]:
                _safety_check(str(ans))

            # ── Actually run the filled code ──────────────────────
            answers_list = [str(a) for a in data["correct_answers"]]
            filled       = data["template_code"]
            for ans in answers_list:
                filled = filled.replace("______", ans, 1)

            stdout, stderr, rc = _run_code(filled)

            if rc != 0:
                raise ValueError(f"Filled code crashes with: {stderr[:200]}")
            if not stdout:
                raise ValueError("Filled code produces no output — needs print()")

            data["answers_list"]    = answers_list
            data["correct_answer"]  = filled
            data["expected_output"] = stdout
            data["topic"]           = topic
            data["difficulty"]      = difficulty
            data["test_cases"]      = [
                {"input": None, "expected_output": stdout},
                {"input": None, "expected_output": stdout},
                {"input": None, "expected_output": stdout},
            ]
            return data

        except Exception as e:
            last_error = str(e)
            prompt = base_prompt + (
                f"\n\n[ATTEMPT {attempt + 1} FAILED — reason: {last_error[:200]}]"
                f"\nThe puzzle you generated was rejected. Redesign it completely "
                f"with different code structure and different blanks."
            )

    raise ValueError(
        f"Question generation failed after 4 attempts. Last error: {last_error}"
    )


# ══════════════════════════════════════════════════════════════
# AGENT 2 — Sandbox Code Analysis
# Runs student code, gives compact 2-line explanation
# ══════════════════════════════════════════════════════════════

def sandbox_analysis_agent(template_code: str, user_answers: list,
                            expected_output: str, topic: str) -> dict:
    """
    Agent 2: Executes student's filled code in real Python sandbox.
    Returns result + 2-sentence LLM explanation.
    """
    user_filled = template_code
    for ans in user_answers:
        user_filled = user_filled.replace("______", str(ans), 1)

    stdout, stderr, rc = _run_code(user_filled)
    sandbox_passed = (rc == 0 and stdout.strip() == expected_output.strip())

    explanation = ""
    if not sandbox_passed:
        actual = stdout if rc == 0 else stderr
        try:
            explanation = _call_llm(
                f"Python student got wrong answer. Write exactly 2 short sentences "
                f"explaining what went wrong. No bullet points. No code.\n\n"
                f"Topic: {topic}\n"
                f"Student code:\n{user_filled}\n"
                f"Expected: {expected_output}\n"
                f"Actual: {actual[:200]}",
                max_tokens=120
            ).strip()
        except Exception:
            explanation = (
                f"Expected '{expected_output}' but got '{(stdout or stderr)[:60]}'. "
                f"Review your {topic} logic."
            )

    return {
        "sandbox_passed":  sandbox_passed,
        "user_output":     stdout if rc == 0 else "",
        "expected_output": expected_output,
        "runtime_error":   stderr if rc != 0 else None,
        "explanation":     explanation,
    }


# ══════════════════════════════════════════════════════════════
# AGENT 3 — LLM Answer Verifier  (PRIMARY checker)
# ══════════════════════════════════════════════════════════════

def llm_verifier_agent(topic: str, difficulty: str,
                        problem_statement: str, template_code: str,
                        correct_answers: list, user_answers: list,
                        sandbox_result: dict) -> dict:
    """
    Agent 3: Primary correctness checker.
    Sandbox passed → correct. Sandbox failed → check if alternative solution.
    """
    user_filled    = template_code
    correct_filled = template_code
    for u, c in zip(user_answers, correct_answers):
        user_filled    = user_filled.replace("______", str(u), 1)
        correct_filled = correct_filled.replace("______", str(c), 1)

    if sandbox_result.get("sandbox_passed"):
        sb_ctx = "Sandbox PASSED — correct output produced."
    elif sandbox_result.get("runtime_error"):
        sb_ctx = f"Sandbox FAILED — runtime error: {sandbox_result['runtime_error'][:150]}"
    else:
        sb_ctx = (
            f"Sandbox FAILED — expected '{sandbox_result.get('expected_output','')}' "
            f"but got '{sandbox_result.get('user_output','')}'"
        )

    prompt = f"""You are a Python answer verifier for a student learning game.

Topic: {topic} | Difficulty: {difficulty}
Problem: {problem_statement}

Correct answer(s): {" | ".join(f'"{a}"' for a in correct_answers)}
Student's answer(s): {" | ".join(f'"{a}"' for a in user_answers)}

Correct filled code:
{correct_filled}

Student's filled code:
{user_filled}

Sandbox: {sb_ctx}

RULES:
- sandbox passed → is_correct = true
- student code solves problem correctly via different approach → is_correct = true, is_alternative = true
- wrong logic or wrong output → is_correct = false
- runtime/syntax error → is_correct = false

VERDICT RULE — CRITICAL:
- NEVER reveal the correct answer, correct code, or correct value in the verdict
- If incorrect: explain WHY the student's approach is wrong conceptually, without showing the correct answer
- If correct: briefly affirm what they did right

Return ONLY this JSON:
{{
  "is_correct": true or false,
  "is_alternative": true or false,
  "verdict": "one clear sentence for the student — no correct answer revealed"
}}"""

    try:
        raw    = _call_llm(prompt, max_tokens=200)
        result = _extract_json(raw)
        return {
            "is_correct":   bool(result.get("is_correct", False)),
            "is_alternative": bool(result.get("is_alternative", False)),
            "verdict":      str(result.get("verdict", "")),
        }
    except Exception as e:
        return {
            "is_correct":   sandbox_result.get("sandbox_passed", False),
            "is_alternative": False,
            "verdict":      f"Verification error: {str(e)[:60]}",
        }


# ══════════════════════════════════════════════════════════════
# AGENT 4 — Hint Generator  (-10 pts)
# ══════════════════════════════════════════════════════════════

def hint_generator_agent(topic: str, difficulty: str,
                          problem_statement: str, template_code: str,
                          user_answers: list,
                          sandbox_explanation: str,
                          llm_verdict: str) -> str:
    """
    Agent 4: 1-2 sentence hint. Never reveals the answer.
    """
    prompt = (
        f"You are a friendly Python tutor giving a hint. Never reveal the answer.\n"
        f"Topic: {topic} | Difficulty: {difficulty}\n"
        f"Problem: {problem_statement}\n"
        f"Template: {template_code}\n"
        f"Student answered: {' | '.join(str(a) for a in user_answers)}\n"
        f"Sandbox note: {sandbox_explanation}\n"
        f"AI verdict: {llm_verdict}\n\n"
        f"Write 1-2 encouraging sentences nudging toward correct thinking. Plain text only."
    )
    try:
        return _call_llm(prompt, max_tokens=120).strip()
    except Exception:
        return f"Think about which Python {topic} expression or method completes this correctly!"
