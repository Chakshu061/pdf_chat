from parser import parse_pdf, chunk_text
from embedder import Embedder
from retriever import generate_answer
from summarizer import summarize_pdf

def run_pipeline(pdf_path, question=None):
    # Step 1: Parse PDF
    text = parse_pdf(pdf_path)

    # Step 2: Chunk PDF into pieces
    chunks = chunk_text(text)

    # Step 3: Build FAISS index
    retriever = Embedder()
    retriever.build_index(chunks)

    # Step 4: If question is given → Q&A, else → full summary
    if question:
        answer = generate_answer(question, retriever, text)
    else:
        answer = summarize_pdf(text)

    return answer

if __name__ == "__main__":
    pdf_file = "short-stories-for-children-ingles-primaria-continuemos-estudiando.pdf"  # use your resume here

    # 1️⃣ Full summary of resume
    print("\n=== Summary ===\n")
    print(run_pipeline(pdf_file))

    # 2️⃣ Q&A examples
    print("\n=== Q&A: Key Skills ===\n")
    print(run_pipeline(pdf_file, "Summarise the story"))

