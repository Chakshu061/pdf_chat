import fitz  # PyMuPDF
import re
from typing import List

def parse_pdf(file_path: str) -> str:
    """Extract text from PDF with better structure preservation and error handling."""
    try:
        doc = fitz.open(file_path)
        text = ""
        
        print(f"PDF has {doc.page_count} pages")
        
        for page_num, page in enumerate(doc):
            try:
                # Get text with layout info
                page_text = page.get_text("text")
                
                # If no text found, try different extraction method
                if not page_text or len(page_text.strip()) < 10:
                    print(f"Page {page_num + 1}: No text found, trying 'dict' method")
                    # Try dict method for better text extraction
                    blocks = page.get_text("dict")
                    page_text = ""
                    for block in blocks.get("blocks", []):
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line.get("spans", []):
                                    page_text += span.get("text", "") + " "
                
                # Add page markers for better chunking
                if page_num > 0:
                    text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
                
                text += page_text if page_text else f"[Page {page_num + 1} - No extractable text]"
                
                print(f"Page {page_num + 1}: Extracted {len(page_text)} characters")
                
            except Exception as page_error:
                print(f"Error processing page {page_num + 1}: {page_error}")
                text += f"\n\n--- PAGE {page_num + 1} ---\n\n[Error extracting text from this page]\n\n"
        
        doc.close()
        
        # Final validation
        if not text or text.isspace():
            print("WARNING: No text extracted from PDF")
            return "[No text could be extracted from this PDF. It may be image-based or corrupted.]"
        
        print(f"Total extracted text: {len(text)} characters")
        return text
        
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return f"[Error reading PDF: {e}]"

# Keep your original function for backward compatibility
def chunk_text(text, chunk_size=1000, overlap=100):
    """Split text into chunks with overlap (your original function)."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def smart_chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    """Enhanced chunking that respects document structure."""
    
    # First, split by major sections (headers, page breaks)
    major_sections = re.split(r'\n\n--- PAGE \d+ ---\n\n|\n\n(?=[A-Z][A-Z\s]{10,})\n', text)
    
    chunks = []
    current_chunk = ""
    
    for section in major_sections:
        # Split section into paragraphs
        paragraphs = section.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    
                    # Start new chunk with overlap
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    # Paragraph itself is too long, split it
                    chunks.extend(_split_long_paragraph(paragraph, chunk_size, overlap))
                    current_chunk = ""
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return [chunk for chunk in chunks if len(chunk.strip()) > 50]  # Filter out tiny chunks

def _split_long_paragraph(paragraph: str, chunk_size: int, overlap: int) -> List[str]:
    """Split a long paragraph into smaller chunks."""
    sentences = re.split(r'[.!?]+\s+', paragraph)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                # Add overlap from previous chunk
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
            else:
                # Even single sentence is too long, force split
                words = sentence.split()
                for i in range(0, len(words), chunk_size//10):
                    chunk_words = words[i:i + chunk_size//10]
                    chunks.append(" ".join(chunk_words))
                current_chunk = ""
        else:
            current_chunk += ". " + sentence if current_chunk else sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks