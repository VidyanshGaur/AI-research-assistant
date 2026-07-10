# 📄 AI Research Assistant

A RAG (Retrieval-Augmented Generation) pipeline that lets you upload research papers and interact with them through natural language — ask questions, generate summaries, compare papers, and download structured reports.

## Features

- **Q&A** — Ask natural language questions, get answers grounded in the paper with source chunks shown
- **Summarization** — Concise (150-200 words) or structured (Problem / Methodology / Results / Conclusion)
- **Paper Comparison** — Upload two papers, get a structured side-by-side comparison
- **Report Generation** — Auto-generate and download a full structured research report as `.md`

## Tech Stack

| Component | Tool |
|---|---|
| LLM | Groq API (Llama 3.1-8b-instant) |
| Orchestration | LangChain |
| Embeddings | HuggingFace sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | FAISS |
| PDF Parsing | PyMuPDF |
| Frontend | Streamlit |

## How It Works

1. PDF uploaded → text extracted via PyMuPDF
2. Text split into overlapping chunks (1000 tokens, 200 overlap)
3. Each chunk embedded using `all-MiniLM-L6-v2`
4. Chunks indexed in FAISS for fast semantic search
5. On query → top-k chunks retrieved → passed to Llama 3.1 via Groq
6. Answer grounded in retrieved context (no hallucination guesswork)

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/ai-research-assistant
cd ai-research-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

GROQ_API_KEY=your_groq_api_key_here

Run:
```bash
streamlit run app.py
```

## Project Structure
ai-research-assistant/
├── app.py              # Streamlit frontend
├── rag_engine.py       # Core RAG pipeline
├── requirements.txt    # Dependencies
├── .env                # API keys (not committed)
└── .gitignore

## Known Limitations

- Retrieval depends on top-k chunk selection — abstract-level questions occasionally miss the most relevant chunk
- Comparison tab requires processing papers one at a time due to Streamlit state management
- No persistent vector store — re-indexes on each upload

## Future Improvements

- Persistent FAISS index storage
- Multi-document Q&A
- Streaming responses
- HuggingFace Spaces deployment