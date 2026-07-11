"""
Secure Sandbox Executor — handles ALL comparison edge cases + multiple blanks
"""

import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from typing import List, Optional

from flask import current_app


@dataclass
class TestResult:
    test_index: int
    input_expr: Optional[str]
    expected_output: str
    actual_output: str
    passed: bool
    error: Optional[str] = None


@dataclass
class ExecutionResult:
    all_passed: bool
    test_results: List[TestResult] = field(default_factory=list)
    error: Optional[str] = None


FORBIDDEN_PATTERNS = [
    (r"\bimport\b",         "import statements are not allowed"),
    (r"\b__[a-zA-Z]+__\b", "dunder attributes are not allowed"),
    (r"\beval\b",           "eval() is not allowed"),
    (r"\bexec\b",           "exec() is not allowed"),
    (r"\bopen\b",           "open() is not allowed"),
    (r"\bcompile\b",        "compile() is not allowed"),
    (r"\bglobals\b",        "globals() is not allowed"),
    (r"\blocals\b",         "locals() is not allowed"),
]


def _check_safety(code: str) -> Optional[str]:
    for pattern, message in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return f"Security violation: {message}"
    return None


def _normalize_collection(s: str) -> str:
    s = re.sub(r'\s*,\s*', ',', s)
    s = re.sub(r'\s*:\s*', ':', s)
    s = re.sub(r'\s*\[\s*', '[', s)
    s = re.sub(r'\s*\]\s*', ']', s)
    s = re.sub(r'\s*\{\s*', '{', s)
    s = re.sub(r'\s*\}\s*', '}', s)
    s = re.sub(r'\s*\(\s*', '(', s)
    s = re.sub(r'\s*\)\s*', ')', s)
    return s.strip()


def _normalize(s: str) -> str:
    s = str(s).strip()
    s = ' '.join(s.split())
    s = s.strip("'\"")
    return s.lower()


def _normalize_lines(s: str) -> list:
    return [line.strip() for line in s.splitlines() if line.strip()]


def smart_compare(actual: str, expected: str) -> bool:
    """10-strategy smart comparison."""
    a = str(actual).strip()
    e = str(expected).strip()

    if a == e: return True
    if a.lower() == e.lower(): return True
    if _normalize(a) == _normalize(e): return True
    try:
        if abs(float(a) - float(e)) < 1e-9: return True
    except (ValueError, TypeError):
        pass
    none_like = {'none', 'null', ''}
    if a.lower() in none_like and e.lower() in none_like: return True
    if _normalize_collection(a) == _normalize_collection(e): return True
    al = _normalize_lines(a)
    el = _normalize_lines(e)
    if al and el and al == el: return True
    if al and el and [x.lower() for x in al] == [x.lower() for x in el]: return True
    # Semicolon-separated vs newline
    a_semi = '\n'.join(a.split(';')).strip()
    e_semi = '\n'.join(e.split(';')).strip()
    if a_semi == e_semi: return True
    return False


def _fill_template(template_code: str, answers: list) -> str:
    """Fill all blanks in template with answers list."""
    code = template_code
    # Normalize semicolons to newlines
    code = code.replace(';', '\n')
    for ans in answers:
        code = code.replace("______", str(ans), 1)
    return code


def _build_script(full_code: str, test_case: dict) -> str:
    input_expr = test_case.get("input")
    if input_expr and str(input_expr).strip() not in ("", "null", "None"):
        return textwrap.dedent(f"""
{full_code}

_result = {input_expr}
if _result is not None:
    print(_result)
""").strip()
    return full_code


def _run(script: str, timeout: int, python: str):
    try:
        proc = subprocess.run(
            [python, "-c", script],
            capture_output=True, text=True, timeout=timeout
        )
        return proc.stdout.strip(), proc.stderr.strip(), proc.returncode, False
    except subprocess.TimeoutExpired:
        return "", "Timeout", -1, True
    except Exception as ex:
        return "", str(ex), -1, False


def execute_code(user_code: str, template_code: str,
                 test_cases: list, correct_answer: str = None,
                 user_answers: list = None) -> ExecutionResult:
    """
    Execute user code against all test cases.
    Supports multiple blanks via user_answers list.
    """
    # Normalize blank variations
    template_code = re.sub(r'_{3,}', '______', template_code)
    if "______" not in template_code:
        return ExecutionResult(all_passed=False,
                               error="Template missing blank placeholder.")

    # Build full user code
    if user_answers and len(user_answers) > 1:
        full_code = _fill_template(template_code, user_answers)
    else:
        full_code = template_code.replace(";", "\n").replace("______", user_code, 1)

    safety_error = _check_safety(full_code)
    if safety_error:
        return ExecutionResult(all_passed=False, error=safety_error)

    timeout = current_app.config.get("SANDBOX_TIMEOUT", 3)
    python = sys.executable

    # Pre-run correct answer for dynamic comparison
    dynamic_outputs = {}
    if correct_answer:
        correct_code = correct_answer.replace(";", "\n")
        if not _check_safety(correct_code):
            for i, tc in enumerate(test_cases):
                script = _build_script(correct_code, tc)
                stdout, _, rc, _ = _run(script, timeout, python)
                if rc == 0 and stdout:
                    dynamic_outputs[i] = stdout

    test_results = []
    all_passed = True

    for i, tc in enumerate(test_cases):
        script = _build_script(full_code, tc)
        stored_expected = str(tc.get("expected_output", "")).strip()
        dynamic_expected = dynamic_outputs.get(i)
        best_expected = dynamic_expected if dynamic_expected else stored_expected

        stdout, stderr, returncode, timed_out = _run(script, timeout, python)

        if timed_out:
            test_results.append(TestResult(
                test_index=i, input_expr=tc.get("input"),
                expected_output=best_expected, actual_output="",
                passed=False, error="Time limit exceeded"
            ))
            all_passed = False
            continue

        if returncode != 0:
            test_results.append(TestResult(
                test_index=i, input_expr=tc.get("input"),
                expected_output=best_expected, actual_output="",
                passed=False, error=f"Runtime error: {stderr[:300]}"
            ))
            all_passed = False
            continue

        passed = (
            smart_compare(stdout, stored_expected) or
            (dynamic_expected is not None and smart_compare(stdout, dynamic_expected))
        )

        if not passed:
            all_passed = False

        test_results.append(TestResult(
            test_index=i, input_expr=tc.get("input"),
            expected_output=best_expected,
            actual_output=stdout,
            passed=passed
        ))

    return ExecutionResult(all_passed=all_passed, test_results=test_results)