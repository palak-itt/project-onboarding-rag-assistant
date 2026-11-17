import json, os
from .answer import rag_answer
from app.rag.store import search
from .embedding import generate_embeddings

def run():
    items = json.load(open("data/project/hp_omni/easyticket/evals/easyticket_eval.json"))
    rows= []
    for i,item in enumerate(items):
        query = item["question"]
        embedded_q = generate_embeddings(query)
        print(rag_answer(query, embedded_q))
        

run()