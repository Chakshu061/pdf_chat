from typing import List
from llm import query_llm

class HierarchicalSummarizer:
    def __init__(self, full_text: str, chunks: List[str]):
        self.full_text = full_text
        self.chunks = chunks
        self.chunk_summaries = []
        self.final_summary = ""
    
    def generate_summary(self) -> str:
        """Generate summary using hierarchical approach."""
        
        print("Starting hierarchical summarization...")
        
        # Step 1: Summarize chunks in batches
        batch_size = 5
        self.chunk_summaries = []
        
        for i in range(0, min(len(self.chunks), 20), batch_size):  # Limit to first 20 chunks
            batch_chunks = self.chunks[i:i + batch_size]
            batch_text = "\n\n".join(batch_chunks)
            
            prompt = f"Summarize this section concisely:\n\n{batch_text[:2000]}"
            summary = query_llm(prompt, model="llama3")
            self.chunk_summaries.append(summary)
            print(f"Summarized batch {i//batch_size + 1}")
        
        # Step 2: Combine summaries
        combined_summaries = "\n\n".join(self.chunk_summaries)
        
        prompt = f"Create a comprehensive summary from these section summaries:\n\n{combined_summaries}"
        self.final_summary = query_llm(prompt, model="llama3")
        
        print("Summary generation complete!")
        return self.final_summary
    
    def generate_faqs(self, num_questions: int = 5) -> str:
        """Generate FAQs based on the document content."""
        
        # Use final summary if available, otherwise use first few chunks
        content = self.final_summary if self.final_summary else "\n\n".join(self.chunks[:3])
        
        prompt = f"""Based on this content, generate {num_questions} frequently asked questions with detailed answers:

{content[:2000]}

Format as:
Q1: [Question]
A1: [Answer]

Q2: [Question] 
A2: [Answer]

etc."""
        
        return query_llm(prompt, model="llama3")