
import ollama
import json

from .answer import rag_answer
from .embedding import generate_embeddings


def judge(eval_obj):
    query = eval_obj["question"]
    expected_answer = eval_obj["expected_answer"]
    # expt_src = eval_obj["source"]
    expected_behavior = eval_obj["expected_behavior"]
    embedded_q = generate_embeddings(query)
    actual_answer = rag_answer(query, embedded_q)
    print(actual_answer)
    print()
    prompt = f"""
You are an independent evaluator for a RAG system.

Evaluate the generated answer against the reference answer.

Question: {query}

Expected behavior: {expected_behavior}

Reference answer:
{expected_answer}

Generated answer:
{actual_answer}

Evaluation rules:

1. If expected_behavior is 'abstain':
   - abstained_correctly: The model says it doesn't know or
     clearly states that the information is unavailable.
   - failed_to_abstain: The model invents an answer or makes
     unsupported claims.

2. If expected_behavior is 'answer':
   - correct: All important facts are correct.
   - partially_correct: Some facts are correct, but important
     information is missing or inaccurate.
   - incorrect: The answer is wrong or unrelated.
   - abstained: The model refuses despite the answer being available.

    Do not demand identical wording.
    Judge semantic meaning, not exact text.

    Return ONLY valid JSON:
    {{
        "verdict": "correct",
        "explanation": "Brief reason"
    }}
    """
    response = ollama.chat(
        model="qwen2.5:3b",
        messages= [{"role": "user", "content": prompt}],
        format= "json",
        options={"temperature": 0}
    )

    return json.loads(response["message"]["content"])


