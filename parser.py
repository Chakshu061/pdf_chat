import fitz  # PyMuPDF

def parse_pdf(file_path):
    """Extract text from PDF and return as one big string."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def chunk_text(text, chunk_size=1000, overlap=100):
    """Split text into chunks with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
