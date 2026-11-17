import chromadb
# import PathLib
from .embedding import generate_embeddings
client = chromadb.PersistentClient(path="./chromadb")

collection = client.get_or_create_collection(name="hp-omni_easyticket_v1", metadata={"hnsw:space": "cosine"})

def print_collection():
    data = collection.get(include=["documents", "metadatas"])
    for id, doc, meta in zip(data["ids"], data["documents"], data["metadatas"]):
        print(f"{id} -> {doc} | {meta}")

def store(chunks, source="easyticket/public/README.md"):
    batch_size = 32
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start: start+batch_size]
        embeddings = generate_embeddings(batch)
        ids =[f"{source}-chunk-{i}" for i in range(start, start+len(batch))]
        metadatas = [
            {"source": source,
             "chunk_index": i} for i in range(start, start+len(batch))
        ]
        collection.upsert(ids=ids,
                          documents=batch,
                          embeddings=embeddings,
                          metadatas=metadatas)

        print(f"Stored {len(chunks)} chunks to {collection.name}.")
        print(f"Total collection count is {collection.count()}")
        print_collection()

def search(query, k=5, where=None):
    r = collection.query(query_embeddings=query, n_results=k, where=where)
    return [dict(id=i, text=d, meta=m, score=round(1-dist, 3)) for i,d,m,dist in zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0])]
