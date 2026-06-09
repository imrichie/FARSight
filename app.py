# app.py
# FARSight — Streamlit frontend entrypoint.
# Minimal shell: structure only, no styling.
# A Figma design will be applied in a later milestone.

import streamlit as st
from src.regulation_retriever import retrieve_relevant_regulation_chunks
from src.answer_generator import generate_cited_answer

st.title("FARSight")
st.caption("Ask a question about FAA regulations. Answers are cited directly from the FAR/AIM.")

user_question = st.text_input(label="Your question", placeholder="e.g. What are the visibility requirements for VFR flight in Class B airspace?")

if st.button("Ask") and user_question:
    with st.spinner("Searching the FAR/AIM..."):
        retrieved_regulation_chunks = retrieve_relevant_regulation_chunks(user_question)
        cited_answer = generate_cited_answer(user_question, retrieved_regulation_chunks)

    st.subheader("Answer")
    st.write(cited_answer["answer_text"])

    if cited_answer["answer_was_found"]:
        st.subheader("Source")
        st.write(f"{cited_answer['citation_source_document']} — {cited_answer['citation_section_identifier']}, p. {cited_answer['citation_page_number']}")
