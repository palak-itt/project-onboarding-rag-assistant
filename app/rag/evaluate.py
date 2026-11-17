
import ollama
import json
from pathlib import Path

from .answer import rag_answer
from .embedding import generate_embeddings  # Adjust to your actual embedding function


DATASET = Path("easyticket_v3_evaluation_set.json")
OUTPUT = Path("evaluation_results.json")


JUDGE_PROMPT = """
You are an independent evaluator of a RAG system.

Evaluate the generated answer against the reference answer
and the retrieved context.

Question:
{question}

Reference answer:
{expected}

Generated answer:
{actual}

Retrieved context:
{context}

Expected behavior: {behavior}

Evaluate these dimensions:

1. Correctness:
   Does the generated answer convey the important facts
   in the reference answer?

2. Faithfulness:
   Are the claims in the generated answer supported
   by the retrieved context?

3. Abstention:
   If expected behavior is "abstain", did the model
   correctly refuse to answer?
   If expected behavior is "answer", did it answer
   rather than unnecessarily refusing?

Use these verdicts:
- correct
- partially_correct
- incorrect
- abstained
- abstained_correctly
- failed_to_abstain

Return ONLY JSON in this structure:

{
    "correctness": "correct",
    "faithfulness": "faithful",
    "abstention": "not_applicable",
    "verdict": "correct",
    "explanation": "Short explanation"
}

For faithfulness use:
- faithful
- partially_faithful
- unfaithful

For abstention use:
- abstained_correctly
- failed_to_abstain
- not_applicable

Do not reward an answer just because it sounds plausible.
Use only the retrieved context as evidence.
"""


def evaluate_with_qwen(question, expected, actual, context, behavior):

    prompt = JUDGE_PROMPT.format(
        question=question,
        expected=expected,
        actual=actual,
        context=context,
        behavior=behavior
    )

    response = ollama.chat(
        model="qwen2.5:3b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        format="json",
        options={"temperature": 0}
    )

    return json.loads(response["message"]["content"])


def run_evaluation():

    with open(DATASET, encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []

    for i, case in enumerate(test_cases, 1):

        question = case["question"]

        # Generate query embedding using your existing model.
        embedded_q = embed_query(question)

        # Run the RAG pipeline.
        rag_result = rag_answer(question, embedded_q)

        actual = rag_result["answer"]
        hits = rag_result["hits"]

        # Reconstruct the retrieved context for the judge.
        context = "\n\n".join(
            f"[{j+1}] {h['text']}"
            for j, h in enumerate(hits)
        )

        # Independent evaluation using Qwen.
        evaluation = evaluate_with_qwen(
            question=question,
            expected=case["expected_answer"],
            actual=actual,
            context=context,
            behavior=case["expected_behavior"]
        )

        result = {
            "id": case["id"],
            "question": question,
            "expected": case["expected_answer"],
            "actual": actual,
            "retrieved_sources": [
                h["meta"]["source"] for h in hits
            ],
            **evaluation
        }

        results.append(result)

        print(f"\n[{i}/{len(test_cases)}] {case['id']}")
        print("Answer:", actual)
        print("Correctness:", evaluation["correctness"])
        print("Faithfulness:", evaluation["faithfulness"])
        print("Verdict:", evaluation["verdict"])

        # Save progressively so completed evaluations aren't lost.
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n========== FINAL RESULTS ==========")

    print("Total:", len(results))

    for metric in ["correctness", "faithfulness", "verdict"]:
        print(f"\n{metric.upper()}")

        from collections import Counter
        counts = Counter(r[metric] for r in results)

        for label, count in counts.items():
            print(f"{label}: {count}")

    print("\nSaved to:", OUTPUT)


if __name__ == "__main__":
    run_evaluation()
