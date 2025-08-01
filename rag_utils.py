__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

VECTORSTORE_DIR = "chromastore"

def ingest_files(uploaded_files):
    docs = []
    for f in uploaded_files:
        text = f.read().decode("utf-8", errors="ignore")
        docs.append(text)
    embeds = OpenAIEmbeddings()
    store = Chroma.from_texts(
        texts=docs,  
        embedding_function=embeds,  
        persist_directory=VECTORSTORE_DIR
    )
    return store

def load_retriever():
    return Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=OpenAIEmbeddings()
    ).as_retriever()
