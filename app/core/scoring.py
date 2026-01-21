def score_quiz(quiz: dict, answers: dict) -> dict:
    """
    answers: {question_id: selected_index}
    returns: {
      "total": int,
      "correct": int,
      "incorrect_questions": [question objects...]
    }
    """
    questions = quiz["questions"]
    correct = 0
    incorrect = []

    for q in questions:
        qid = q["id"]
        selected = answers.get(qid, None)
        if selected is not None and selected == q["correctIndex"]:
            correct += 1
        else:
            incorrect.append(q)

    return {
        "total": len(questions),
        "correct": correct,
        "incorrect_questions": incorrect
    }
