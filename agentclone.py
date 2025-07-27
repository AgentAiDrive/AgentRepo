import os, uuid, json, asyncio
import streamlit as st
from pydantic import BaseModel, Field
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
PERSONAS_FILE = "personas.json"

class Persona(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    source_type: str
    source: str
    short_description: str
    tools_enabled: list
    memory_enabled: bool
    knowledge_sources: list

def load_personas():
    if os.path.exists(PERSONAS_FILE):
        return [Persona(**p) for p in json.load(open(PERSONAS_FILE))]
    return []

def save_personas(personas):
    with open(PERSONAS_FILE, "w") as f:
        json.dump([p.dict() for p in personas], f, indent=2)

async def generate_short_desc(agent_type, source_type, source):
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":"You generate concise agent persona descriptions."},
            {"role":"user","content":
             f"Generate a concise (≤200 characters) description of an agent type '{agent_type}' "
             f"using knowledge from {source_type}: {source}. Focus on domain expertise only."}
        ],
        temperature=0.3, max_tokens=80
    )
    return resp.choices[0].message.content.strip()

def make_system_prompt(persona):
    tools = ", ".join(persona.tools_enabled) if persona.tools_enabled else "no extra tools"
    memory = "with memory" if persona.memory_enabled else "without memory"
    knowledge = f"Additional knowledge sources: {persona.knowledge_sources}" if persona.knowledge_sources else ""
    return (
        f"You are {persona.name}, a {persona.type} using {persona.source_type} ({persona.source}).\n"
        f"Expertise: {persona.short_description}\n"
        f"Tools enabled: {tools}, {memory}. {knowledge}"
    )

# --- Top nav bar ---
pages = ["Home", "Agents", "Create Agent", "Chats"]
if "page" not in st.session_state:
    st.session_state.page = "Home"
nav_cols = st.columns(len(pages))
for i, label in enumerate(pages):
    if nav_cols[i].button(label):
        st.session_state.page = label
        st.rerun()

if st.session_state.page == "Home":
    st.title("Agent Clone Wizard")
    st.write("Welcome! Use the top nav to create or manage agents and chat with your AI clones.")

elif st.session_state.page == "Agents":
    st.title("Your Agents")
    personas = load_personas()
    for p in personas:
        with st.container():
            st.markdown(f"**{p.name}** ({p.type}) – {p.short_description}")
            st.write(f"Tools: {', '.join(p.tools_enabled) or 'None'}; Memory: {p.memory_enabled}")
            st.write(f"Sources: {', '.join(p.knowledge_sources) or 'None'}")
            if st.button("Delete", key=p.id):
                personas = [x for x in personas if x.id != p.id]
                save_personas(personas)
                st.rerun()

elif st.session_state.page == "Create Agent":
    st.title("Create New Agent Persona")

    with st.form("step1"):
        st.subheader("Basic Info & Source")
        name = st.text_input("Persona name")
        agent_type = st.text_input("Agent type (e.g. Research Assistant)")
        source_type = st.selectbox("Source type", ["File", "URL"])
        source = st.text_input("Source (file path or URL)")
        submitted = st.form_submit_button("Generate Description")
    if submitted:
        if name and agent_type and source:
            desc = asyncio.run(generate_short_desc(agent_type, source_type, source))
            st.session_state.generated_desc = desc
            st.session_state.meta = dict(name=name, type=agent_type, source_type=source_type, source=source)
        else:
            st.warning("Please fill all fields.")

    if st.session_state.get("generated_desc"):
        with st.container():
            st.write("**Generated description:**")
            st.write(st.session_state.generated_desc)
            col1, col2, col3 = st.columns(3)
            if col1.button("Approve"):
                st.session_state.short_desc = st.session_state.generated_desc
            if col2.button("Edit"):
                st.session_state.short_desc = st.text_input("Edit description", st.session_state.generated_desc)
            if col3.button("Retry"):
                st.session_state.pop("generated_desc")
                st.rerun()

    if st.session_state.get("short_desc"):
        with st.form("step2"):
            st.subheader("Tools & Memory")
            tools = st.multiselect("Select tools:", ["web_search","file_search","code"])
            mem = st.checkbox("Enable session memory")
            knowledge = st.text_area("Knowledge sources (one per line)")
            submitted2 = st.form_submit_button("Save Persona")
        if submitted2:
            persona = Persona(
                id=str(uuid.uuid4()),
                name=st.session_state.meta["name"],
                type=st.session_state.meta["type"],
                source_type=st.session_state.meta["source_type"],
                source=st.session_state.meta["source"],
                short_description=st.session_state.short_desc,
                tools_enabled=tools,
                memory_enabled=mem,
                knowledge_sources=[s.strip() for s in knowledge.splitlines() if s.strip()]
            )
            ps = load_personas()
            ps.append(persona)
            save_personas(ps)
            st.success("Persona saved!")
            st.session_state.pop("generated_desc", None)
            st.session_state.pop("short_desc", None)

elif st.session_state.page == "Chats":
# <-- AGENTS SDK
    st.title("Chat with an Agent")
    personas = load_personas()
    if not personas:
        st.info("No agents available. Create one first!")
    else:
        agent_names = [f"{p.name} ({p.type})" for p in personas]
        idx = st.selectbox("Choose an agent:", range(len(agent_names)), format_func=lambda i: agent_names[i])
        persona = personas[idx]
        st.markdown(f"**Talking to {persona.name} ({persona.type})**")
        st.caption(persona.short_description)

        # --- AGENT SDK SESSION ---
        if "agent_sessions" not in st.session_state:
            st.session_state.agent_sessions = {}
        if persona.id not in st.session_state.agent_sessions:
            # Build the agent using OpenAI's beta.agents.Agent
            tools_to_use = []
            if "web_search" in persona.tools_enabled:
                tools_to_use.append(oa_agents.WebSearchTool())
            if "file_search" in persona.tools_enabled:
                tools_to_use.append(oa_agents.FileSearchTool())
            if "code" in persona.tools_enabled:
                tools_to_use.append(oa_agents.CodeInterpreterTool())

            agent = oa_agents.Agent(
                name=persona.name,
                instructions=make_system_prompt(persona),
                tools=tools_to_use,
                model_config={"model": "gpt-4o", "temperature": 0.5}
            )
            chat_session = oa_agents.ChatSession(agent)
            st.session_state.agent_sessions[persona.id] = chat_session
            st.session_state.chat_history = []
        else:
            chat_session = st.session_state.agent_sessions[persona.id]

        # --- Display chat history ---
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for m in st.session_state.chat_history:
            st.chat_message(m["role"]).write(m["content"])

        if prompt := st.chat_input("Say something..."):
            st.session_state.chat_history.append({"role":"user", "content": prompt})
            with st.spinner("Thinking... (using real agent tools)"):
                # AGENTS SDK: Real tool-calling chat session!
                result = asyncio.run(chat_session.run(prompt))
                output = getattr(result, "final_output", None)
                if output:
                    st.session_state.chat_history.append({"role": "assistant", "content": output})
                    st.chat_message("assistant").write(output)
                else:
                    st.session_state.chat_history.append({"role": "assistant", "content": "No response."})
                    st.chat_message("assistant").write("No response.")
