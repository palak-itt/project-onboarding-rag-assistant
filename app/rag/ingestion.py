from .chunking import fixed_chunks
from .store import store
# import PathLib

file_path = "data/project/hp_omni/easyticket/public/README.md"

def ingest(content):
    chunks = fixed_chunks(content)
    print(f"Total chunks = {len(chunks)}")
    store(chunks)

if __name__== "__main__":
    with open(file_path, "r", encoding="utf-8") as file:
        file_content = file.read()
    ingest(file_content)
    print("Successfully ingested.")

