from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List

class OptimizedEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []
        
    def build_index(self, chunks: List[str]):
        """Build FAISS index with batch processing."""
        self.chunks = chunks
        
        # Process embeddings in batches to avoid memory issues
        batch_size = 32
        all_embeddings = []
        
        print(f"Processing {len(chunks)} chunks in batches of {batch_size}...")
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = self.model.encode(batch_chunks, convert_to_numpy=True)
            all_embeddings.append(batch_embeddings)
            print(f"Processed batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
        
        # Combine all embeddings
        embeddings_array = np.vstack(all_embeddings)
        dimension = embeddings_array.shape[1]
        
        # Build FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        print(f"Index built with {self.index.ntotal} vectors")
    
    def query(self, question: str, top_k: int = 5) -> List[str]:
        """Query the index for relevant chunks."""
        if self.index is None:
            return []
        
        # Get embedding for question
        q_embedding = self.model.encode([question], convert_to_numpy=True)
        
        # Search
        distances, indices = self.index.search(q_embedding, min(top_k, len(self.chunks)))
        
        # Return relevant chunks
        results = []
        for idx in indices[0]:
            if idx != -1:  # Valid index
                results.append(self.chunks[idx])
        
        return results