import ollama
from .store import search


def rag_answer(question, embedded_q):
    hits = search(embedded_q)
    ctx = "\n\n".join(f"[{i+1}] (source: {h['meta']['source']})\n{h['text']}" for i, h in enumerate(hits))

    # 3. Prepare prompt
    prompt = f"""
    Answer the question using only the context below.

    If the context does not contain the answer, say you don't know.

    Context:
    {ctx}

    Question: {question}

    Answer:
    """
    response = ollama.chat(
        model="llama3.2:3b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0.2}
    )

    return {
        "answer": response["message"]["content"],
        "hits": hits
    }