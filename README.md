# AgentRepo
repository for agent ai
https://agentclone.streamlit.app/

## Quick Start

1. `pip install -r requirements.txt`
2. `streamlit run app.py`
3. Use the tab navigation to add sources, build agents, upload documents (RAG), and chat.

## Modules

- `app_utils.py`: Source and profile helpers.
- `rag_utils.py`: RAG file ingestion & retrieval.
- `memory.py`: Chat memory (session & persistent).
- `functions.py`: OpenAI-callable function hooks.
- `agentclone.py`: Main app UI.



# **📘 My Parent Helpers — User Guide**

## 1. Getting Started

* Open the app at **agentclone.streamlit.app**.
* At the top you’ll see:

  * A **memory toggle** (Session only / Persistent).
  * A **“Clear Session”** button to reset state if needed.
* Below, you’ll find **five tabs** for different stages: **Agents**, **Sources**, **RAG**, **Chat**, and **History**.

## 📄 Summary Table

| Tab     | Purpose                                        |
| ------- | ---------------------------------------------- |
| Agents  | #2 Create/select your parenting agent          |
|                                                          |
| Sources | #3 Manage grounding sources (books/experts)    |
|                                                          |
| RAG     | #4 Upload documents for retrieval context      |  
|                                                          |
| Chat    | #5 Chat with your agent, optionally use RAG    |
|                                                          |
| History | #6 Review saved conversations (persistent only)|
|                                                          |
| Memory  | #7 Set persistent memory, clear data           |
| ------- | ---------------------------------------------- |

---

## 2. 🚀 Agents Tab: Building & Selecting Your Personal Assistant

* Name your agent, choose profile settings:

  * **Agent Type**: Parent, Teacher, or Other
  * **Persona Name**
  * **Tone**: Warm, Directive, Playful, or Clinical
  * **Parent Name**, **Child Name**, and **Child Age**
  * Select any grounding sources from your custom list (`Sources` tab)
* Click **“Create Agent”** to save.
* Below, select the **active agent** via a dropdown.
* The chosen agent's details display in JSON format.

---

## 3. 📚 Sources Tab: Add or Edit Grounding Sources

* Source categories (Books, Experts, Styles, Custom) are editable.
* Add or remove entries using the text entry boxes.
* Click **“Save Sources”** to update.
* These sources will be used in your agent’s system prompt during chats.

---

## 4. 📂 RAG Tab: Upload Documents for Contextual Retrieval

* Upload your documents (TXT or PDF).
* Click **“Ingest Files”** to index them via retrieval embeddings.
* The top 2 relevant document chunks are available during chat if context is enabled.

---

## 5. 💬 Chat Tab: Chat With Your Agent

* Ensure an agent is selected in the Agents tab.
* Write your parenting question or scenario in the input box.
* Optionally check **“Retrieve from uploaded docs”** to include document-based context.
* Click **Send** to submit. The logic:

  1. Two-layer prompting uses persona + sources, plus past memory and RAG docs.
  2. If the model triggers a function call (`retrieve_documents`), it fetches context and re‑asks.
  3. The reply is displayed as:

     * **You:** your input
     * **Agent name:** model-generated response
* Responses append to chat memory (session or persistent depending on memory mode).

---

## 6. 🕑 History Tab: Review All Conversations

* Displays full conversation history for all agents (if using **Persistent** memory).
* Each agent’s history is shown under its own heading.
* Interactions show in order: You → Agent reply.

---

## 7. Memory & Clearing Options

* **Memory toggle** (top of page):

  * **Session only**: memory persists only during browser session.
  * **Persistent**: history saved across restarts (using `chat_history.json`).
* **Clear Session** button: wipes all session\_state, including active agent and session memory.

---

## ✅ Sample Workflow Example

1. Select **“Session only”** memory.
2. Go to **Sources** — add favorite books or expert names.
3. Go to **Agents** — build an agent named “GentleParent” using those sources.
4. Go to **Chat** — send a question like “How to calm a toddler tantrum?”
5. Optionally check **RAG** if you’ve uploaded parenting articles.
6. Receive advice tailored to your profile.
7. Visit **History** to review previous chats when ready.

---

## ⚙️ Troubleshooting Tips

* **If you see** “Please set your OpenAI API key…”: Set the key via **Streamlit Secrets** or your environment variable.
* **No documents are retrieving?** Ensure you’ve ingested at least one TXT/PDF in the RAG tab.
* **Agent dropdown missing?** Create at least one agent in the Agents tab and save it.
