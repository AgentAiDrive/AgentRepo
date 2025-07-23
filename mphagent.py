import streamlit as st
import openai, json, os
from pydantic import BaseModel

# ---------------------------------------------------------------------------
#  \U0001F4D0  GLOBAL STYLE SHEET
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    body{background:linear-gradient(135deg,#2fe273 0%,#09742a 100%)!important;min-height:100vh;}
    .stApp{
      background:linear-gradient(335deg,#2fe273 0%,#09742a 100%)!important;
      border-radius:32px;
      max-width:400px;
      min-height:730px;
      margin:32px auto;
      box-shadow:0 8px 32px rgba(60,60,60,.25),0 1.5px 8px rgba(30,90,40,.06);
      border:3px solid #ffffff;
      display:flex;
      flex-direction:column;
      align-items:center;
      padding:10px 10px 10px;
    }
    .biglabel{font-size:1.4em;font-weight:800;color:#ffffff;margin:4px 0 10px;text-align:center;letter-spacing:.5px;}
    .frame-avatar{font-size:1.4em;margin:6px 0 6px;display:flex;justify-content:center;color:#ffffff;}

    .stButton>button{
      border-radius:26px!important;
      font-weight:700!important;
      font-size:.9em!important;
      padding:.8em 0!important;
      background:#27e67a!important;
      color:#ffffff!important;
      margin:6px 0!important;
      width:100%!important;
    }
    .top-nav-container {
      padding: 12px 12px 12px 12px !important;
      border-radius: 32px !important;
      margin: -10px -10px 24px -10px !important;
      width: calc(100% + 20px) !important;
    }

    /* --- Top nav button colors: HIGH SPECIFICITY! --- */
    .top-nav-container > div[data-testid="stHorizontalBlock"] > div > div[data-testid="stButton"][data-key="nav_home"] > button { background: #e63946 !important; }
    .top-nav-container > div[data-testid="stHorizontalBlock"] > div > div[data-testid="stButton"][data-key="nav_chat"] > button { background: #27e67a !important; }
    .top-nav-container > div[data-testid="stHorizontalBlock"] > div > div[data-testid="stButton"][data-key="nav_saved"] > button { background: #1d3557 !important; }

    /* --- Answer bubble --- */
    .answer-box{background:#23683c;border-radius:12px;padding:14px 18px;color:#fff;white-space:pre-wrap;margin-top:8px;}
    @media (max-height:750px){.stApp{min-height:640px;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
#  TOP NAVIGATION
# ---------------------------------------------------------------------------
def render_top_nav():
    st.markdown('<div class="top-nav-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("\U0001F3E0 Home", key="nav_home"):
            st.session_state.step = 0
            st.rerun()
    with col2:
        if st.button("\U0001F4AC Chat", key="nav_chat"):
            st.session_state.step = 6 if st.session_state.profiles else 1
            st.rerun()
    with col3:
        if st.button("\U0001F4C2 Saved", key="nav_saved"):
            if st.session_state.saved_responses:
                st.session_state.step = 7
            else:
                st.warning("No saved responses yet.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
#  HELPER FUNCTIONS & CONSTANTS
# ---------------------------------------------------------------------------
PROFILES_FILE = "parent_helpers_profiles.json"
RESPONSES_FILE = "parent_helpers_responses.json"

def load_json(path: str):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return []

def save_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Error writing {path}: {e}")

for key, default in {
    "profiles":        load_json(PROFILES_FILE),
    "saved_responses": load_json(RESPONSES_FILE),
    "last_answer":     "",
}.items():
    st.session_state.setdefault(key, default)

step = st.session_state.get("step", 0)
openai.api_key = st.secrets.get("openai_key", "YOUR_OPENAI_API_KEY")

BOOKS = [
    "Parenting with Presence", "Parenting Without Power Struggles",
    "Peaceful Parent, Happy Kids", "Permission to Parent",
    "Positive Parenting: An Essential Guide", "Punished by Rewards"
]
EXPERTS = [
    "Dr. Laura Markham", "Dr. Daniel Siegel", "Dr. Ross Greene",
    "Janet Lansbury", "Adele Faber"
]
STYLES = [
    "Positive Parenting", "Authoritative", "Permissive",
    "Attachment Parenting", "Montessori", "Gentle Parenting"
]

class PersonaProfile(BaseModel):
    profile_name: str
    parent_name: str
    child_name: str
    child_age: int
    source_type: str
    source_name: str
    persona_description: str

SHORTCUTS = ["\U0001F4AC DEFAULT","\U0001F91D CONNECT","\U0001F331 GROW","\U0001F50D EXPLORE","\U0001F6E0 RESOLVE","❤ SUPPORT"]
EMOJIS = {"\U0001F4AC DEFAULT":"\U0001F4AC","\U0001F91D CONNECT":"\U0001F91D","\U0001F331 GROW":"\U0001F331","\U0001F50D EXPLORE":"\U0001F50D","\U0001F6E0 RESOLVE":"\U0001F6E0","❤ SUPPORT":"❤"}
TOOLTIPS = {
    "\U0001F4AC DEFAULT":"No formatting",
    "\U0001F91D CONNECT":"Help explain complex ideas with examples",
    "\U0001F331 GROW":"Strategies to improve parenting",
    "\U0001F50D EXPLORE":"Age-appropriate Q&A",
    "\U0001F6E0 RESOLVE":"Step-by-step advice",
    "❤ SUPPORT":"Empathetic guidance"
}

# ---------------------------------------------------------------------------
#  STEP LOGIC
# ---------------------------------------------------------------------------
if step == 0:
    st.markdown(
        """
        <div style="text-align:center;">
          <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="160" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    row1c1, row1c2 = st.columns(2)
    with row1c1:
        if st.button("SAVED PROFILES", key="home_profiles"):
            if st.session_state.profiles:
                st.session_state.step = 8
                st.rerun()
            else:
                st.warning("No profiles yet.")
    with row1c2:
        if st.button("NEW PROFILE", key="home_create"):
            st.session_state.step = 1
            st.rerun()
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    row2c1, row2c2 = st.columns(2)
    with row2c1:
        if st.button("CHAT", key="home_chat"):
            st.session_state.step = 6 if st.session_state.profiles else 1
            if not st.session_state.profiles:
                st.warning("No profiles – create one first.")
            st.rerun()
    with row2c2:
        if st.button("SAVED CHATS", key="home_saved"):
            if st.session_state.saved_responses:
                st.session_state.step = 7
                st.rerun()
            else:
                st.warning("No saved responses yet!")

elif step == 1:
    render_top_nav() 
    st.markdown(
            """
            <div style="text-align:center;">
              <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="80" />
            </div>
            """,
            unsafe_allow_html=True,)
    st.markdown('<div class="biglabel">Select A Parenting Source Type</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("\U0001F4DA  Book", key="btn_book"):
            st.session_state.source_type = "Book"
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("\U0001F9D1‍  Expert", key="btn_expert"):
            st.session_state.source_type = "Expert"
            st.session_state.step = 2
            st.rerun()
    with col3:
        if st.button("\U0001F31F  Style", key="btn_style"):
            st.session_state.source_type = "Style"
            st.session_state.step = 2
            st.rerun()

elif step == 2:
    st.markdown(
                """
                <div style="text-align:center;">
                  <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="80" />
                </div>
                """,
                unsafe_allow_html=True,) 
    st.markdown(f'<div class="biglabel">Choose a {st.session_state.source_type}</div>', unsafe_allow_html=True)
    options = BOOKS if st.session_state.source_type == "Book" else EXPERTS if st.session_state.source_type == "Expert" else STYLES
    emoji = "\U0001F4DA" if st.session_state.source_type == "Book" else "\U0001F9D1‍" if st.session_state.source_type == "Expert" else "\U0001F31F"
    st.markdown(f'<div class="frame-avatar">{emoji}</div>', unsafe_allow_html=True)
    choice = st.selectbox("Select or enter your own:", options + ["Other..."])
    custom = st.text_input("Enter custom name") if choice == "Other..." else ""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("BACK", key="btn_back_step2"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("CREATE", key="btn_create_step2"):
            src_name = custom if choice == "Other..." else choice
            if not src_name:
                st.warning("Please provide a name.")
            else:
                st.session_state.source_name = src_name
                st.session_state.step = 3
                st.rerun()

elif step == 3:
    st.markdown(
        """
        <div style="text-align:center;">
            <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="80" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    import time
    st.markdown('<div class="biglabel">GENERATING YOUR PARENTING AGENT PERSONA</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar">\U0001F9E0✨</div>', unsafe_allow_html=True)
    placeholder = st.empty()
    for msg in ["Assimilating Knowledge…", "Synthesizing Information…", "Assessing Results…", "Generating Persona…"]:
        placeholder.info(msg)
        time.sleep(0.5)
    if "persona_description" not in st.session_state:
        with st.spinner("Thinking…"):
            try:
                prompt = (
                    f"Summarize the parenting philosophy, core principles, and practices of "
                    f"the {st.session_state.source_type} '{st.session_state.source_name}' in under 200 words. "
                    "Respond in a JSON object with 'persona_description'."
                )
                out = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                raw = out.choices[0].message.content
                st.session_state.persona_description = json.loads(raw)["persona_description"]
            except Exception as e:
                st.error(f"OpenAI API error: {e}")
    placeholder.empty()
    desc = st.session_state.get("persona_description")
    if desc:
        st.info(desc)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("RETRY", key="btn_retry"):
            st.session_state.pop("persona_description", None)
            st.rerun()
    with col2:
        if st.button("SAVE", key="btn_save_persona"):
            st.session_state.step = 4
            st.rerun()

elif step == 4:
    st.markdown(
                """
                <div style="text-align:center;">
                  <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="80" />
                </div>
                """,
                unsafe_allow_html=True,)
    st.markdown('<div class="biglabel">PARENTING AGENT DETAILS</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar">\U0001F4F7</div>', unsafe_allow_html=True)
    with st.form("profile"):
        p_name = st.text_input("Parent first name")
        c_age  = st.number_input("Child age", 1, 21)
        c_name = st.text_input("Child first name")
        prof_nm= st.text_input("Profile name")
        saved  = st.form_submit_button("SAVE")
    if saved:
        if not all([p_name, c_age, c_name, prof_nm]):
            st.warning("Please fill every field.")
        else:
            profile = PersonaProfile(
                profile_name=prof_nm,
                parent_name=p_name,
                child_name=c_name,
                child_age=int(c_age),
                source_type=st.session_state.source_type,
                source_name=st.session_state.source_name,
                persona_description=st.session_state.persona_description
            )
            st.session_state.profiles.append(profile.dict())
            save_json(PROFILES_FILE, st.session_state.profiles)
            st.success("Profile saved!")
            st.session_state.step = 5
            st.rerun()
    if st.button("BACK", key="btn_back_details"):
        st.session_state.step = 3
        st.rerun()
elif step == 5:
    st.markdown(
            """
            <div style="text-align:center;">
              <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="80" />
            </div>
            """,
            unsafe_allow_html=True,)
    render_top_nav() 
    st.markdown('<div class="biglabel">PARENTING AGENT PROFILE CREATED! \U0001F389</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar">\U0001F4DD\U0001F389</div>', unsafe_allow_html=True)

elif step == 6:
    st.markdown(
                """
                <div style="text-align:center;">
                  <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="80" />
                </div>
                """,
                unsafe_allow_html=True,)
    render_top_nav() 
    st.markdown('<div class="biglabel">1. SELECT A PARENTING AGENT</div>', unsafe_allow_html=True)
    names = [p["profile_name"] for p in st.session_state.profiles]
    col_dd, col_icon = st.columns([4,1])
    idx = col_dd.selectbox("Parenting Agent Profiles:", range(len(names)),
                          format_func=lambda i: names[i], key="chat_profile")
    sel = st.session_state.profiles[idx]
    tooltip = (
        f"Profile: {sel['profile_name']} "
        f"Type: {sel['source_type']} "
        f"Source: {sel['source_name']} "
        f"Child: {sel['child_name']} "
        f"Age: {sel['child_age']} "
        f"Parent: {sel['parent_name']} "
        f"Persona: {sel['persona_description']}"
    )
    col_icon.markdown(
        f'<span title="{tooltip}" style="font-size:1.5em; cursor:help;">ℹ️</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div style="
          background: #d3d3d3;
          padding: 12px;
          border-radius: 8px;
          margin-top: 12px;
        ">
          <div style="margin-bottom:8px;">
            <span style="color:#27e67a;font-weight:700;font-size:1.2em;">ACTIVE AGENT</span>
          </div>
          <div style="display:flex;justify-content:space-between;flex-wrap:wrap;">
            <div><span style="color:#27e67a;font-weight:600;">Profile:</span>
                 <span style="color:#000;font-weight:500;">{sel['profile_name']}</span></div>
            <div><span style="color:#27e67a;font-weight:600;">Source:</span>
                 <span style="color:#000;font-weight:500;">{sel['source_name']}</span></div>
            <div><span style="color:#27e67a;font-weight:600;">Child Age:</span>
                 <span style="color:#000;font-weight:500;">{sel['child_age']}</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="biglabel">2. SELECT A RESPONSE TYPE</div>', unsafe_allow_html=True)
    st.session_state.setdefault("shortcut", "\U0001F4AC DEFAULT")
    cols = st.columns(len(SHORTCUTS))
    for i, sc in enumerate(SHORTCUTS):
        with cols[i]:
            if st.button(EMOJIS[sc], key=f"type_{sc}", help=TOOLTIPS[sc]):
                st.session_state.shortcut = sc
    st.markdown(
        f"""
        <div style="background:#fff;color:#000;padding:12px;border-radius:8px;margin-top:12px;margin-bottom:12px;">
          <strong>Selected:</strong> {st.session_state.shortcut}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="biglabel">3. WHAT DO YOU WANT TO ASK?</div>', unsafe_allow_html=True)
    query = st.text_area("Type here", key="chat_query")
    if st.session_state.last_answer:
        st.markdown(f"<div class='answer-box'>{st.session_state.last_answer}</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("SAVE RESPONSE", key="save_response"):
            record = {
                "profile": sel["profile_name"],
                "shortcut": st.session_state.shortcut,
                "question": query,
                "answer":   st.session_state.last_answer
            }
            if record not in st.session_state.saved_responses:
                st.session_state.saved_responses.append(record)
                save_json(RESPONSES_FILE, st.session_state.saved_responses)
            st.session_state.step = 7
            st.rerun()
    with col2:
        if st.button("SEND", key="send_btn"):
            base = (
              f"You are a parenting coach with persona: {sel['persona_description']}."
              f" Parent: {sel['parent_name']}, Child: {sel['child_name']}, Age: {sel['child_age']}."
            )
            extra_map = {
              "\U0001F91D CONNECT":" Help explain with examples.",
              "\U0001F331 GROW":" Offer advanced strategies.",
              "\U0001F50D EXPLORE":" Facilitate age-appropriate Q&A.",
              "\U0001F6E0 RESOLVE":" Provide step-by-step resolution.",
              "❤ SUPPORT":" Offer empathetic support."
            }
            prompt = base + extra_map.get(st.session_state.shortcut, "") + "\n" + query + "\nRespond as JSON with 'answer'."
            try:
                out = openai.chat.completions.create(
                  model="gpt-4o",
                  messages=[{"role":"system","content":prompt}],
                  response_format={"type":"json_object"}
                )
                st.session_state.last_answer = json.loads(out.choices[0].message.content)["answer"]
            except Exception as e:
                st.error(f"OpenAI API error: {e}")
            st.rerun()

elif step == 7:
    st.markdown(
                """
                <div style="text-align:center;">
                  <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="80" />
                </div>
                """,
                unsafe_allow_html=True,)
    render_top_nav() 
    st.markdown('<div class="biglabel">SELECT A SAVED CHAT</div>', unsafe_allow_html=True)
    if not st.session_state.saved_responses:
        st.info("No saved responses."); st.session_state.step = 0; st.rerun()
    titles = [f"{i+1}. {r['profile']} – {r['shortcut']}" for i, r in enumerate(st.session_state.saved_responses)]
    sel_idx = st.selectbox("Saved Chats:", range(len(titles)), format_func=lambda i: titles[i], key="saved_select")
    item = st.session_state.saved_responses[sel_idx]
    for field in ("profile","shortcut"):
        st.markdown(f'''
          <p style="color:#fff;margin:4px 0;">
            <strong>{field.title()}:</strong> {item[field]}
          </p>''', unsafe_allow_html=True)
    st.markdown('''
      <p style="color:#fff;margin:4px 0;"><strong>Question:</strong></p>''',
      unsafe_allow_html=True)
    st.markdown(f'''
      <blockquote style="color:#fff;border-left:4px solid #27e67a;
                        padding-left:8px;margin:4px 0;">
        {item["question"]}
      </blockquote>''', unsafe_allow_html=True)
    st.markdown('''
      <p style="color:#fff;margin:4px 0;"><strong>Answer:</strong></p>''',
      unsafe_allow_html=True)
    st.markdown(f'''
      <div class="answer-box" style="color:#fff;">
        {item["answer"]}
      </div>''', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("DELETE", key="btn_delete_saved"):
            st.session_state.saved_responses.pop(sel_idx)
            save_json(RESPONSES_FILE, st.session_state.saved_responses)
            st.rerun()
    with c2:
        if st.button("CLOSE", key="btn_close_saved"):
            st.session_state.step = 0
            st.rerun()

elif step == 8:
    st.markdown(
                """
                <div style="text-align:center;">
                  <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png" width="80" />
                </div>
                """,
                unsafe_allow_html=True,)
    render_top_nav() 
    st.markdown('<div class="biglabel">MY PROFILES</div>', unsafe_allow_html=True)
    if not st.session_state.profiles:
        st.info("No profiles stored."); st.session_state.step = 0; st.rerun()
    titles = [f"{i+1}. {p['profile_name']}" for i,p in enumerate(st.session_state.profiles)]
    idx = st.selectbox("Select a profile to view / edit", range(len(titles)), format_func=lambda i: titles[i], key="profile_select")
    prof = st.session_state.profiles[idx]
    with st.form("edit_profile"):
        p_name = st.text_input("Parent first name", value=prof["parent_name"])
        c_age  = st.number_input("Child age", 1, 21, value=prof["child_age"])
        c_name = st.text_input("Child first name", value=prof["child_name"])
        prof_nm= st.text_input("Profile name", value=prof["profile_name"])
        desc   = st.text_area("Persona description", value=prof["persona_description"], height=150)
        saved  = st.form_submit_button("SAVE CHANGES")
    if saved:
        prof.update(parent_name=p_name, child_age=int(c_age), child_name=c_name, profile_name=prof_nm, persona_description=desc)
        st.session_state.profiles[idx] = prof
        save_json(PROFILES_FILE, st.session_state.profiles)
        st.success("Profile updated!")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("DELETE PROFILE", key="btn_delete_profile"):
            st.session_state.profiles.pop(idx)
            save_json(PROFILES_FILE, st.session_state.profiles)
            st.rerun()
    with c2:
        if st.button("CLOSE", key="btn_close_profile"):
            st.session_state.step = 0
            st.rerun()   ### this is the updated code that works.
