import streamlit as st
import tempfile
import os
from rag_engine import process_pdf, generate_summary, compare_papers, generate_report

st.set_page_config(page_title="AI Research Assistant", layout="wide")

st.title("📄 AI Research Assistant")
st.caption("Upload research papers to ask questions, summarize, or compare them.")

# ---- Session state setup ----
for key in ["processed", "chat_history", "summary", "processed_a", "processed_b", "comparison"]:
    if key not in st.session_state:
        st.session_state[key] = None
if st.session_state.chat_history is None:
    st.session_state.chat_history = []

def process_uploaded_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    result = process_pdf(tmp_path)
    os.unlink(tmp_path)
    return result

# ---- Sidebar: PDF upload (single-paper workflows) ----
with st.sidebar:
    st.header("Upload Paper")
    uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

    if uploaded_file is not None:
        if st.button("Process PDF"):
            with st.spinner("Reading and indexing the paper... this may take a minute"):
                st.session_state.processed = process_uploaded_pdf(uploaded_file)
                st.session_state.chat_history = []
                st.session_state.summary = None
            st.success("Paper processed! Use the tabs to explore.")

# ---- Main area ----
tab_qa, tab_summary, tab_report, tab_compare = st.tabs(["💬 Ask Questions", "📝 Summarize", "📊 Report", "⚖️ Compare Papers"])

# ---- Q&A TAB ----
with tab_qa:
    if st.session_state.processed is None:
        st.info("👈 Upload a PDF in the sidebar and click 'Process PDF' to get started.")
    else:
        question = st.text_input("Ask a question about the paper:")

        if st.button("Ask") and question:
            with st.spinner("Thinking..."):
                qa_chain = st.session_state.processed["qa_chain"]
                result = qa_chain.invoke({"query": question})
                answer = result["result"]
                sources = result["source_documents"]
            st.session_state.chat_history.append((question, answer, sources))

        for q, a, sources in reversed(st.session_state.chat_history):
            st.markdown(f"**Q: {q}**")
            st.markdown(a)
            with st.expander("📚 Source chunks used"):
                for i, doc in enumerate(sources):
                    st.markdown(f"**Chunk {i+1}:**")
                    st.text(doc.page_content[:300] + "...")
            st.divider()

# ---- SUMMARIZE TAB ----
with tab_summary:
    if st.session_state.processed is None:
        st.info("👈 Upload a PDF in the sidebar and click 'Process PDF' to get started.")
    else:
        detail_level = st.radio(
            "Summary style:",
            options=["concise", "detailed"],
            format_func=lambda x: "Concise (150-200 words)" if x == "concise" else "Detailed (structured sections)",
            horizontal=True
        )

        if st.button("Generate Summary"):
            with st.spinner("Reading through the paper and summarizing... this can take a minute or two"):
                chunks = st.session_state.processed["chunks"]
                llm = st.session_state.processed["llm"]
                try:
                    st.session_state.summary = generate_summary(chunks, llm, detail_level)
                except Exception as e:
                    st.error(f"Summary generation failed: {e}")

        if st.session_state.summary:
            st.markdown("### Summary")
            st.markdown(st.session_state.summary)

# ---- REPORT TAB ----
with tab_report:
    if st.session_state.processed is None:
        st.info("👈 Upload a PDF in the sidebar and click 'Process PDF' to get started.")
    else:
        st.markdown("Generate a comprehensive structured report for the uploaded paper.")

        paper_name = st.text_input("Paper name (for the report title):", value="Research Paper")

        if st.button("Generate Report"):
            with st.spinner("Generating full report — this will take 2-3 minutes..."):
                chunks = st.session_state.processed["chunks"]
                qa_chain = st.session_state.processed["qa_chain"]
                llm = st.session_state.processed["llm"]
                try:
                    report = generate_report(chunks, qa_chain, llm, paper_name)
                    st.session_state["report"] = report
                except Exception as e:
                    st.error(f"Report generation failed: {e}")

        if st.session_state.get("report"):
            st.markdown("### Generated Report")
            st.markdown(st.session_state["report"])
            st.download_button(
                label="⬇️ Download Report (.md)",
                data=st.session_state["report"],
                file_name=f"{paper_name.replace(' ', '_')}_report.md",
                mime="text/markdown"
            )

# ---- COMPARE TAB ----
with tab_compare:
    st.markdown("Upload two papers to compare their goals, methods, and findings.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Paper A")
        file_a = st.file_uploader("Choose Paper A", type="pdf", key="paper_a")
        if file_a is not None and st.button("Process Paper A"):
            with st.spinner("Processing Paper A..."):
                st.session_state.processed_a = process_uploaded_pdf(file_a)
            st.success("Paper A ready!")

    with col2:
        st.subheader("Paper B")
        file_b = st.file_uploader("Choose Paper B", type="pdf", key="paper_b")
        if file_b is not None and st.button("Process Paper B"):
            with st.spinner("Processing Paper B..."):
                st.session_state.processed_b = process_uploaded_pdf(file_b)
            st.success("Paper B ready!")

    st.divider()

    if st.session_state.processed_a and st.session_state.processed_b:
        if st.button("Compare Papers"):
            with st.spinner("Summarizing both papers and generating comparison... this may take a few minutes"):
                chunks_a = st.session_state.processed_a["chunks"]
                chunks_b = st.session_state.processed_b["chunks"]
                llm = st.session_state.processed_a["llm"]  # reuse one llm instance
                try:
                    st.session_state.comparison = compare_papers(chunks_a, chunks_b, llm)
                except Exception as e:
                    st.error(f"Comparison failed: {e}")

        if st.session_state.comparison:
            st.markdown("### Comparison")
            st.markdown(st.session_state.comparison)
    else:
        st.info("Process both Paper A and Paper B above to enable comparison.")