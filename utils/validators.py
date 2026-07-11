def validate_topic(topic: str) -> str:
    topic = (topic or "").strip()
    if not topic or len(topic) < 2:
        raise ValueError("Topic is required.")
    if len(topic) > 200:
        raise ValueError("Topic too long.")
    return topic

def validate_difficulty(difficulty: str) -> str:
    difficulty = (difficulty or "").strip().lower()
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("Difficulty must be easy, medium, or hard.")
    return difficulty

def validate_user_answer(answer) -> str:
    answer = (answer or "").strip()
    if not answer:
        raise ValueError("Answer is required.")
    if len(answer) > 2000:
        raise ValueError("Answer too long.")
    return answer
