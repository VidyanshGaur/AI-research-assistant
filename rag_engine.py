import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv

load_dotenv()

# ---- Step 1: Extract text from PDF ----
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

# ---- Step 2: Split text into chunks ----
def split_text(text, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)
    return chunks

# ---- Step 3: Create embeddings + FAISS vector store ----
def create_vector_store(chunks):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(chunks, embeddings)
    return vector_store

# ---- Step 4: Build the RAG QA chain ----
def build_qa_chain(vector_store, llm):
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True
    )
    return qa_chain

# ---- Step 5: Summarization prompts ----
MAP_PROMPT = PromptTemplate(
    template=(
        "Summarize the following excerpt from a research paper in 2-3 sentences, "
        "focusing on the key information:\n\n{text}\n\nSUMMARY:"
    ),
    input_variables=["text"]
)

CONCISE_COMBINE_PROMPT = PromptTemplate(
    template=(
        "The following are summaries of sections from a research paper. "
        "Combine them into a single, coherent summary of 150-200 words that "
        "captures the paper's purpose, method, and key findings. "
        "Output ONLY the summary text itself — no preamble, no meta-commentary "
        "like 'here is a summary', and no mention of word count.\n\n"
        "{text}\n\nSUMMARY:"
    ),
    input_variables=["text"]
)

DETAILED_COMBINE_PROMPT = PromptTemplate(
    template=(
        "The following are summaries of sections from a research paper. "
        "Using them, write a structured summary with these exact headings:\n\n"
        "**Problem Statement**\n**Methodology**\n**Key Results**\n**Conclusion**\n\n"
        "Output ONLY the structured summary — no preamble or meta-commentary.\n\n"
        "Section summaries:\n{text}\n\nSTRUCTURED SUMMARY:"
    ),
    input_variables=["text"]
)

def generate_summary(chunks, llm, detail_level="concise"):
    docs = [Document(page_content=c) for c in chunks]
    combine_prompt = CONCISE_COMBINE_PROMPT if detail_level == "concise" else DETAILED_COMBINE_PROMPT
    chain = load_summarize_chain(
        llm=llm,
        chain_type="map_reduce",
        map_prompt=MAP_PROMPT,
        combine_prompt=combine_prompt
    )
    result = chain.invoke({"input_documents": docs})
    return result["output_text"]

# ---- Step 6: Full pipeline — PDF in, everything out ----
def process_pdf(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text(text)
    vector_store = create_vector_store(chunks)
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant"
    )
    qa_chain = build_qa_chain(vector_store, llm)
    return {
        "chunks": chunks,
        "vector_store": vector_store,
        "llm": llm,
        "qa_chain": qa_chain
    }
# ---- Step 7: Compare two papers ----
COMPARISON_PROMPT = PromptTemplate(
    template=(
        "You are comparing two research papers based on their summaries below.\n\n"
        "PAPER A SUMMARY:\n{summary_a}\n\n"
        "PAPER B SUMMARY:\n{summary_b}\n\n"
        "Write a structured comparison with these exact headings:\n\n"
        "**Problem/Goal Comparison**\n"
        "**Methodology Comparison**\n"
        "**Key Differences**\n"
        "**Which paper suits which use case**\n\n"
        "Output ONLY the structured comparison — no preamble or meta-commentary."
    ),
    input_variables=["summary_a", "summary_b"]
)

def compare_papers(chunks_a, chunks_b, llm):
    summary_a = generate_summary(chunks_a, llm, detail_level="concise")
    summary_b = generate_summary(chunks_b, llm, detail_level="concise")

    prompt = COMPARISON_PROMPT.format(summary_a=summary_a, summary_b=summary_b)
    response = llm.invoke(prompt)
    return response.content
# ---- Step 8: Generate structured report ----
REPORT_QUESTIONS = [
    "What is the main contribution of this paper?",
    "What problem does this paper solve?",
    "What methodology or approach is used?",
    "What datasets were used in the experiments?",
    "What are the key results and findings?",
    "What are the limitations mentioned in the paper?",
]

def generate_report(chunks, qa_chain, llm, paper_name="Research Paper"):
    # Only ONE summary (detailed) — saves ~30 API calls
    detailed = generate_summary(chunks, llm, detail_level="detailed")

    # Auto Q&A — only 4 questions instead of 6
    REPORT_QUESTIONS = [
        "What is the main contribution of this paper?",
        "What methodology or approach is used?",
        "What datasets were used in the experiments?",
        "What are the key results and findings?",
    ]

    qa_pairs = []
    for question in REPORT_QUESTIONS:
        result = qa_chain.invoke({"query": question})
        qa_pairs.append((question, result["result"]))

    # Build markdown report
    report = f"# Research Report: {paper_name}\n\n"
    report += "---\n\n"
    report += "## Structured Summary\n"
    report += detailed + "\n\n"
    report += "---\n\n"
    report += "## Key Questions & Answers\n\n"
    for q, a in qa_pairs:
        report += f"**Q: {q}**\n\n{a}\n\n"
    report += "---\n\n"
    report += f"*Report generated by AI Research Assistant*\n"

    return report