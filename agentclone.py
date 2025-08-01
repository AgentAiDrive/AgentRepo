import streamlit as st
import openai
import os
import json
from app_utils import load_sources, save_sources, load_profiles, save_profiles
from rag_utils import ingest_files, load_retriever
from memory import get_history_path, load_history, save_history
from functions import function_definitions, retrieve_documents
import pysqlite3
import sys
sys.modules['sqlite3'] = pysqlite3

st.set_page_config(page_title="My Parent Helpers", layout="centered")
openai.api_key = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", ""))

if not openai.api_key:
    st.error("Please set your OpenAI API key in your environment or Streamlit secrets.")
    st.stop()

# State for agent selection and memory
if "active_profile" not in st.session_state:
    st.session_state.active_profile = None
if "memory_mode" not in st.session_state:
    st.session_state.memory_mode = "Session only"

# ---- Top-of-page controls ----
with st.container():
    col1, col2 = st.columns([3,1])
    with col2:
        st.session_state.memory_mode = st.radio(
            "Memory", ["Session only", "Persistent"], horizontal=True, key="mem_mode_top"
        )
        if st.button("Clear Session", key="clear_session_top"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.experimental_rerun()

# ---- Tab Navigation ----
tab_labels = ["Agents", "Sources", "RAG", "Chat", "History"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

# ---- AGENTS TAB ----
with tab1:
    st.header("Agent Profile Builder")
    profiles = load_profiles()
    with st.form("new_agent"):
        agent_type = st.selectbox("Agent Type", ["Parent", "Teacher", "Other"])
        persona_name = st.text_input("Profile Name")
        tone = st.selectbox("Tone", ["Warm", "Directive", "Playful", "Clinical"])
        parent_name = st.text_input("Your Name")
        child_name = st.text_input("Child’s Name")
        child_age = st.number_input("Child’s Age", min_value=0, max_value=25, value=7)
        source_list = sum(load_sources().values(), [])
        sources_sel = st.multiselect("Grounding Sources", source_list)
        submit = st.form_submit_button("Create Agent")
        if submit:
            new_prof = {
                "agent_type": agent_type,
                "name": persona_name,
                "tone": tone,
                "sources": sources_sel,
                "parent": parent_name,
                "child": child_name,
                "age": child_age,
            }
            profiles.append(new_prof)
            save_profiles(profiles)
            st.session_state.active_profile = persona_name
            st.success(f"Agent '{persona_name}' created and set as active.")

    st.markdown("#### Select Active Agent")
    if profiles:
        choices = [p['name'] for p in profiles]
        sel = st.selectbox(
            "Profiles", choices,
            index=choices.index(st.session_state.active_profile) if st.session_state.active_profile in choices else 0,
            key="active_profile_select"
        )
        st.session_state.active_profile = sel
        st.write(f"Active: **{sel}**")
        st.json([p for p in profiles if p['name'] == sel][0])
    else:
        st.info("No agent profiles exist. Create one above.")

# ---- SOURCES TAB ----
with tab2:
    sources = load_sources()
    st.header("Edit Domain Sources")
    for cat in sources:
        st.subheader(cat)
        newval = st.text_area(cat, "\n".join(sources[cat]), key=f"src_{cat}")
        sources[cat] = [x.strip() for x in newval.splitlines() if x.strip()]
    if st.button("Save Sources"):
        save_sources(sources)
        st.success("Sources updated.")

# ---- RAG TAB ----
with tab3:
    st.header("Upload and Index Documents")
    files = st.file_uploader("Upload TXT or PDF", accept_multiple_files=True)
    if st.button("Ingest Files") and files:
        ingest_files(files)
        st.success(f"Ingested {len(files)} files into retrieval index.")

# ---- CHAT TAB ----
def build_system_prompt(profile):
    """Layer 1: Persona + sources + key settings"""
    out = [
        f"You are a {profile['agent_type']} parenting assistant named {profile['name']}.",
        f"Your tone is {profile['tone']}.",
        f"Parent: {profile['parent']}  Child: {profile['child']} (Age: {profile['age']})",
        "Use the following sources as your foundation:",
        "; ".join(profile.get('sources', [])),
        "Stay aligned with the selected persona and always use age-appropriate language.",
    ]
    return "\n".join(out)

def assemble_messages(profile, user_input, rag_docs=None, prev_turns=None):
    """Layer 2: Middleware context (RAG, memory)"""
    sys_msg = build_system_prompt(profile)
    messages = [{"role":"system", "content": sys_msg}]
    if rag_docs:
        messages.append({"role": "system", "content": f"Relevant reference: {rag_docs}"})
    if prev_turns:
        for u, b in prev_turns:
            messages.append({"role":"user", "content":u})
            messages.append({"role":"assistant", "content":b})
    messages.append({"role":"user", "content":user_input})
    return messages

with tab4:
    st.header("💬 Chat With Your Helper")
    profiles = load_profiles()
    if not profiles:
        st.warning("Please create and select an Agent profile first in the Agents tab.")
        st.stop()
    active_prof = next((p for p in profiles if p["name"] == st.session_state.active_profile), None)
    if not active_prof:
        st.warning("No active agent profile. Select one in Agents tab.")
        st.stop()
    # Memory mode
    persistent = st.session_state.memory_mode == "Persistent"
    hist_path = get_history_path(persistent)
    prev_turns = load_history(active_prof["name"], hist_path)
    # User input
    user_input = st.text_input("Type your parenting question or scenario:", key="chat_input")
    use_rag = st.checkbox("Retrieve from uploaded docs", value=False)
    
    if st.button("Send") and user_input:
        rag_docs = None
        if use_rag:
            docs = retrieve_documents(user_input)
            if docs:
                rag_docs = "\n\n".join(docs[:2])  # show top 2 docs

        messages = assemble_messages(active_prof, user_input, rag_docs, prev_turns)
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            functions=function_definitions,
            function_call="auto",
            temperature=0.8
        )
        msg = response.choices[0].message

        bot_msg = ""  # Ensure variable is always defined!
        if hasattr(msg, "function_call") and msg.function_call:
            call = msg.function_call
            if call.name == "retrieve_documents":
                args = json.loads(call.arguments)
                docs = retrieve_documents(args["query"])
                messages.append({"role": "system", "content": f"Retrieved Docs:\n{docs}"})
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.8
                )
                bot_msg = response.choices[0].message.content
            else:
                bot_msg = "Function call not handled."
        else:
            bot_msg = msg.content

        prev_turns = prev_turns or []
        prev_turns.append((user_input, bot_msg))
        save_history(active_prof["name"], prev_turns, hist_path)
        st.markdown(f"**You:** {user_input}")
        st.markdown(f"**{active_prof['name']}:** {bot_msg}")

    # Show full chat history
    st.markdown("---")
    st.markdown("#### Conversation History")
    for u, b in (prev_turns or []):
        st.markdown(
            f"<div style='background:#f4fff4;padding:8px;border-radius:8px;margin-bottom:4px'>"
            f"<b>You:</b> {u}<br><b>{active_prof['name']}:</b> {b}</div>",
            unsafe_allow_html=True
        )


# ---- HISTORY TAB ----
with tab5:
    st.header("All Saved Chat Histories")
    profiles = load_profiles()
    persistent = st.session_state.memory_mode == "Persistent"
    hist_path = get_history_path(persistent)
    if not os.path.exists(hist_path or ""):
        st.info("No persistent chat history found.")
    else:
        with open(hist_path) as f:
            all_hist = json.load(f)
        for agent, history in all_hist.items():
            st.markdown(f"### Agent: {agent}")
            for u, b in history:
                st.markdown(f"- **You:** {u}\n    \n  **Agent:** {b}")

# --------------- END OF APP ---------------
