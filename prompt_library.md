# Prompt Library

All prompts used in the AI Research Assistant pipeline.

---

## 1. Map Prompt (Summarization — Phase 1)

**Purpose:** Summarize individual chunks during map-reduce  
**Used in:** Summarization workflow, Report generation

Summarize the following excerpt from a research paper in 2-3 sentences,
focusing on the key information:
{text}
SUMMARY:
---

## 2. Concise Combine Prompt (Summarization — Phase 2)

**Purpose:** Combine chunk summaries into a single 150-200 word paragraph  
**Used in:** Summarize tab (Concise mode), Paper Comparison (pre-step)
The following are summaries of sections from a research paper.
Combine them into a single, coherent summary of 150-200 words that
captures the paper's purpose, method, and key findings.
Output ONLY the summary text itself — no preamble, no meta-commentary
like 'here is a summary', and no mention of word count.
{text}
SUMMARY:**Design note:** "Output ONLY" instruction added after observing LLM adding meta-commentary ("Here is a 150-word summary...") in early testing.

---

## 3. Detailed Combine Prompt (Summarization — Phase 2)

**Purpose:** Combine chunk summaries into a structured 4-section summary  
**Used in:** Summarize tab (Detailed mode), Report generation
The following are summaries of sections from a research paper.
Using them, write a structured summary with these exact headings:
Problem Statement
Methodology
Key Results
Conclusion
Output ONLY the structured summary — no preamble or meta-commentary.
Section summaries:
{text}
STRUCTURED SUMMARY:---

## 4. Comparison Prompt

**Purpose:** Compare two papers based on their concise summaries  
**Used in:** Compare Papers tab

You are comparing two research papers based on their summaries below.
PAPER A SUMMARY:
{summary_a}
PAPER B SUMMARY:
{summary_b}
Write a structured comparison with these exact headings:
Problem/Goal Comparison
Methodology Comparison
Key Differences
Which paper suits which use case
Output ONLY the structured comparison — no preamble or meta-commentary.
---

## 5. QA Retrieval Prompt (Implicit)

**Purpose:** Answer user questions grounded in retrieved chunks  
**Used in:** Ask Questions tab, Report generation (auto Q&A)  
**Type:** LangChain RetrievalQA default chain (stuff type)

Predefined questions used in report generation:
- "What is the main contribution of this paper?"
- "What methodology or approach is used?"
- "What datasets were used in the experiments?"
- "What are the key results and findings?"

---

## Prompt Design Principles

1. **No preamble instruction** — All combine prompts explicitly instruct the model to skip meta-commentary, improving output cleanliness
2. **Exact headings specified** — Structured prompts define exact markdown headings to ensure consistent, parseable output
3. **Context anchoring** — All prompts reference "research paper" context to keep outputs domain-appropriate
4. **Separation of map vs combine** — Two-phase prompting allows chunk-level precision + document-level coherence
