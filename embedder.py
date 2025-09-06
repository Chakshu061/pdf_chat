from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []

    def build_index(self, chunks):
        self.chunks = chunks
        embeddings = self.model.encode(chunks, convert_to_numpy=True)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

    def query(self, question, top_k=5):
        q_embedding = self.model.encode([question], convert_to_numpy=True)
        distances, indices = self.index.search(q_embedding, top_k)
        return [self.chunks[i] for i in indices[0]]
