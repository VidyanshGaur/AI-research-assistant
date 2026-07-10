# Research Workflow

## Overview
This document describes the end-to-end research automation workflow built in the AI Research Assistant project.

---

## Pipeline Architecture
PDF Upload
↓
Text Extraction (PyMuPDF)
↓
Text Chunking (RecursiveCharacterTextSplitter)
chunk_size=1000, chunk_overlap=200
↓
Embedding Generation (HuggingFace all-MiniLM-L6-v2)
↓
Vector Indexing (FAISS)
↓
┌─────────────────────────────────────┐
│         User Query / Action         │
└─────────────────────────────────────┘
↓              ↓              ↓              ↓
Q&A Retrieval   Summarization   Comparison   Report Gen
↓              ↓              ↓              ↓
Top-k chunks    Map-Reduce      Two-paper     Structured
+ Llama 3.1     pipeline        summary       .md report
---

## Workflow 1: Q&A Retrieval

**Input:** User question (natural language)  
**Process:**
1. Query embedded using same `all-MiniLM-L6-v2` model
2. FAISS similarity search → top-5 most relevant chunks retrieved
3. Retrieved chunks + query passed to Llama 3.1-8b-instant via Groq API
4. Answer generated grounded in retrieved context

**Output:** Answer + source chunks shown in UI  
**Prompt type:** RetrievalQA chain (LangChain default)

---

## Workflow 2: Summarization

**Input:** All chunks from uploaded PDF  
**Process (Map-Reduce):**
1. MAP phase — each chunk individually summarized using `MAP_PROMPT`
2. REDUCE phase — all chunk summaries combined using either:
   - `CONCISE_COMBINE_PROMPT` → 150-200 word paragraph
   - `DETAILED_COMBINE_PROMPT` → structured (Problem Statement / Methodology / Key Results / Conclusion)

**Output:** Clean summary with no preamble  
**Design decision:** Map-reduce chosen over stuff chain to handle papers exceeding context window limits

---

## Workflow 3: Paper Comparison

**Input:** Two uploaded PDFs (Paper A and Paper B)  
**Process:**
1. Both papers independently chunked and embedded
2. Concise summary generated for each via map-reduce
3. Both summaries passed to `COMPARISON_PROMPT`
4. LLM generates structured comparison

**Output:** Side-by-side comparison with 4 sections:
- Problem/Goal Comparison
- Methodology Comparison  
- Key Differences
- Which paper suits which use case

---

## Workflow 4: Report Generation

**Input:** Uploaded PDF + user-provided paper name  
**Process:**
1. Detailed structured summary generated (map-reduce)
2. 4 predefined questions automatically run through QA chain:
   - Main contribution
   - Methodology used
   - Datasets used
   - Key results and findings
3. Summary + Q&A compiled into markdown report

**Output:** Downloadable `.md` file with full structured report

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| chunk_size=1000, overlap=200 | Balances context retention vs API call volume |
| k=5 for retrieval | Improved recall for abstract-level questions vs k=3 |
| Map-reduce for summarization | Handles papers of any length without hitting context limits |
| FAISS over ChromaDB | No server setup required, fully local |
| all-MiniLM-L6-v2 | Lightweight, fast, strong semantic similarity performance |

