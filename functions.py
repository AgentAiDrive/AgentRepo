from rag_utils import load_retriever

def retrieve_documents(query: str):
    retriever = load_retriever()
    docs = retriever.get_relevant_documents(query)
    return [doc.page_content for doc in docs]

function_definitions = [
    {
        "name": "retrieve_documents",
        "description": "Fetch relevant text from indexed documents.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
]
