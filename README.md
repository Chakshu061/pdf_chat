# 📄 PDF AI Chat — Summarizer + Chat

A personal project to avoid wading through lengthy PDFs. Upload a PDF, and the app automatically summarizes it, with the option to chat about the document content.  

Initially designed to simplify my own workflow with technical documentation, this project can also scale into use cases like **legal document summarization**, **research papers**, or **corporate knowledge management**.

---
## Demo (Screenshot)
![alt text](<Screenshot 2025-09-09 at 5.11.07 PM.png>)

## 🚀 Features

- 🔹 **PDF Summarization** — Breaks large PDFs into chunks, summarizes each, then merges them into a concise overview.
- 🔹 **Chat with Document** — Ask natural language questions about your uploaded PDF.
- 🔹 **Local LLM Integration** — Runs models like `llama3` via [Ollama](https://ollama.ai/), no API costs.
- 🔹 **React Frontend** — Simple UI for uploading PDFs and chatting ([frontend repo here](https://github.com/Chakshu061/pdf_ai_chat_frontend)).
- 🔹 **FastAPI Backend** — Handles PDF parsing, chunking, querying, and LLM integration.

---

## 🛠️ Tech Stack

### Backend
- [Python](https://www.python.org/) (FastAPI)
- [Ollama](https://ollama.ai/) (local LLM inference)
- PyPDF2 / pdfminer (PDF parsing)
- Custom chunking + summarization pipeline

### Frontend
- [React](https://react.dev/) + Vite
- Redux (state management)
- TailwindCSS (or custom CSS)

### Deployment
- **Backend**: Runs locally with Ollama, can be Dockerized.
- **Frontend**: Deployable for free via [Netlify](https://www.netlify.com/) or [Vercel](https://vercel.com/).

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai/) installed locally
- Node.js 18+ (for frontend)

---

### Backend Setup

```bash
# Clone backend
git clone https://github.com/Chakshu061/pdf_ai_chat_backend
cd pdf_ai_chat_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn main:app --reload
