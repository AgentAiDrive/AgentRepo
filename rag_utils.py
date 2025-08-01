import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

VECTORSTORE_DIR = "vectorstore"

def ingest_files(uploaded_files):
    docs = []
    for f in uploaded_files:
        text = f.read().decode("utf-8", errors="ignore")
        docs.extend(RecursiveCharacterTextSplitter(chunk_size=1000).split_text(text))
    embeds = OpenAIEmbeddings()
    store = FAISS.from_texts(docs, embedder=embeds)
    store.save_local(VECTORSTORE_DIR)
    return store

def load_retriever():
    return FAISS.load_local(VECTORSTORE_DIR, OpenAIEmbeddings()).as_retriever()
