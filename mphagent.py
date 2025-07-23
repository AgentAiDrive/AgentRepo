import streamlit as st
import openai, json, os
from pydantic import BaseModel

# ---------------------------------------------------------------------------
#  📐  GLOBAL STYLE SHEET
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ---------- Global gradient background ---------- */
    body{background:linear-gradient(135deg,#2fe273 0%,#09742a 100%)!important;min-height:100vh;}

    /* ---------- Main card ---------- */
    .stApp{
      background:#1b3b20!important;
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

    /* ---------- Typographic utilities ---------- */
    .biglabel{font-size:1.4em;font-weight:800;color:#ffffff;margin:4px 0 4px;text-align:center;letter-spacing:.5px;}
    .frame-avatar{font-size:1.4em;margin:6px 0 6px;display:flex;justify-content:center;}

    /* ---------- Generic Streamlit button ---------- */
    .stButton>button{
      border-radius:26px!important;
      font-weight:700!important;
      font-size:.8em!important;
      padding:.45em 1.8em!important;
      background:#27e67a!important;
      color:#ffffff!important;
      margin:6px 0;
    }

    /* ---------- Landing-page buttons (key starts with 'home_') ---------- */
    div[data-testid="stButton"][data-key^="home_"] > button{
      width:180px!important;
    }

    /* ---------- Source-type option buttons ---------- */
    div[data-testid="stButton"][data-key^="src_"] > button{
      width:100%!important;
      border-radius:30px!important;
      font-weight:700!important;
      font-size:.9em!important;
      padding:.6em 0!important;
      background:#27e67a!important;
      color:#ffffff!important;
      margin-bottom:8px;
    }
    div[data-testid="stButton"][data-key^="src_"] > button:hover{background:#24c56c!important;}

    /* ---------- Response-type buttons (chat screen) ---------- */
    div[data-testid="stButton"][data-key^="type_"] > button {
      width: 100%           !important;
      border-radius: 30px   !important;
      font-weight: 700      !important;
      font-size: .9em       !important;
      padding: .6em 0       !important;
      background: #27e67a   !important;
      color: #ffffff        !important;
      margin: 4px 0         !important;
    }
    div[data-testid="stButton"][data-key^="type_"] > button:hover {
      background: #24c56c   !important;
    }

    /* ---------- Radio / Select text ---------- */
    .stRadio label,div[data-baseweb=radio] span,.stRadio>label,
    div[role=radiogroup] label,div[role=radiogroup] span{color:#ffffff!important;font-size:1.15em!important;}

    /* ---------- Alerts ---------- */
    .stAlert,.stAlert>div{color:#ffffff!important;background:rgba(39,230,122,.16)!important;border-color:#27e67a!important;}

    /* ---------- Select boxes ---------- */
    .stSelectbox label{color:#ffffff!important;}
    .stSelectbox div[data-baseweb=select]{color:#ffffff!important;background:#23683c!important;}
    .stSelectbox [data-baseweb=menu],.stSelectbox [data-baseweb=option]{background:#23683c!important;color:#ffffff!important;}
    .stSelectbox [data-baseweb=option]:hover,.stSelectbox [aria-selected=true]{background:#27e67a!important;color:#222!important;}

    /* ---------- Inputs ---------- */
    .stTextInput label,.stNumberInput label,.stTextArea label{color:#ffffff!important;}
    .stTextInput input,.stNumberInput input,.stTextArea textarea{color:#000000;background:#ffffff;border-radius:12px;}

    /* ---------- Answer bubble ---------- */
    .answer-box{background:#23683c;border-radius:12px;padding:14px 18px;color:#ffffff;white-space:pre-wrap;margin-top:8px;}

    @media (max-height:750px){.stApp{min-height:640px;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
#  🔧  HELPER FUNCTIONS & CONSTANTS
# ---------------------------------------------------------------------------
PROFILES_FILE = "parent_helpers_profiles.json"
RESPONSES_FILE = "parent_helpers_responses.json"

def load_json(path: str):
    """Load JSON from `path`, return [] on missing file or error."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        st.error(f"Error parsing {path}: {e}")
        return []
    except IOError as e:
        st.error(f"Error reading {path}: {e}")
        return []

def save_json(path: str, data):
    """Write `data` as JSON to `path`, show an error on failure."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        st.error(f"Error writing {path}: {e}")

# Initialize session state from disk
for key, default in {
    "profiles":      load_json(PROFILES_FILE),
    "saved_responses": load_json(RESPONSES_FILE),
    "last_answer":   "",
}.items():
    st.session_state.setdefault(key, default)

step = st.session_state.get("step", 0)

# -------------------- OpenAI --------------------
openai.api_key = st.secrets.get("openai_key", "YOUR_OPENAI_API_KEY")

# -------------------- Constants --------------------
BOOKS = [
    "Parenting with Presence",
    "Parenting Without Power Struggles",
    "Peaceful Parent, Happy Kids",
    "Permission to Parent",
    "Positive Parenting: An Essential Guide",
    "Punished by Rewards",
]

EXPERTS = [
    "Dr. Laura Markham",
    "Dr. Daniel Siegel",
    "Dr. Ross Greene",
    "Janet Lansbury",
    "Adele Faber",
]

STYLES = [
    "Positive Parenting",
    "Authoritative",
    "Permissive",
    "Attachment Parenting",
    "Montessori",
    "Gentle Parenting",
]

class PersonaProfile(BaseModel):
    profile_name: str
    parent_name: str
    child_name: str
    child_age: int
    source_type: str
    source_name: str
    persona_description: str

# ─── STEP 0 – LANDING PAGE ───
if step == 0:
    st.markdown(
        """
       <div style="text-align:center;">
            <img src="https://img1.wsimg.com/isteam/ip/e13cd0a5-b867-446e-af2a-268488bd6f38/myparenthelpers%20logo%20round.png/:/rs=w:200,h:200,cg:true,m/cr=w:200,h:200/qt=q:100/ll" width="160" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ─── First row: Saved Profiles & New Profile ───
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        if st.button(
            "SAVED PROFILES",
            key="home_profiles",
            type="secondary",
            help="SAVED PROFILES",
            use_container_width=True,
        ):
            if st.session_state.profiles:
                st.session_state.step = 8
                st.rerun()
            else:
                st.warning("No profiles yet.")
    with row1_col2:
        if st.button(
            "NEW PROFILE",
            key="home_create",
            type="secondary",
            help="NEW PROFILE",
            use_container_width=True,
        ):
            st.session_state.step = 1
            st.rerun()
            
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ─── Second row: Chat & Saved Chats ───
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        if st.button(
            "CHAT",
            key="home_chat",
            type="secondary",
            help="CHAT",
            use_container_width=True,
        ):
            st.session_state.step = 6 if st.session_state.profiles else 1
            if not st.session_state.profiles:
                st.warning("No profiles – create one first.")
            st.rerun()
    with row2_col2:
        if st.button(
            "SAVED CHATS",
            key="home_saved",
            type="secondary",
            help="SAVED CHATS",
            use_container_width=True,
        ):
            if st.session_state.saved_responses:
                st.session_state.step = 7
                st.rerun()
            else:
                st.warning("No saved responses yet!")


# ================= 1. SOURCE TYPE =================
elif step == 1:
    st.markdown('<div class="biglabel">Select A Parenting Source Type</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar"></div>', unsafe_allow_html=True)

    def option_button(label: str, emoji: str, choice: str):
        clicked = st.button(
            f"{emoji}  {label}",
            key=f"src_{choice}",
            type="primary",
            help=f"Choose {label.lower()} as your parenting source type",
        )
        if clicked:
            st.session_state.source_type = choice
            st.session_state.step = 2
            st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1: option_button("Book", "📚", "Book")
    with col2: option_button("Expert", "🧑‍", "Expert")
    with col3: option_button("Style", "🌟", "Style")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if st.button("BACK TO HOME"): st.session_state.step = 0; st.rerun()

# ================= 2. SOURCE SELECTION =================
elif step == 2:
    st.markdown(f'<div class="biglabel">Choose a {st.session_state.source_type}</div>', unsafe_allow_html=True)

    if st.session_state.source_type == "Book":
        options, emoji = BOOKS, "📚"
    elif st.session_state.source_type == "Expert":
        options, emoji = EXPERTS, "🧑‍"
    else:
        options, emoji = STYLES, "🌟"

    st.markdown(f'<div class="frame-avatar">{emoji}</div>', unsafe_allow_html=True)

    choice = st.selectbox("Select or enter your own:", options + ["Other..."])
    custom = st.text_input("Enter custom name") if choice == "Other..." else ""

    if st.button("CREATE"):
        src_name = custom if choice == "Other..." else choice
        if not src_name:
            st.warning("Please provide a name.")
        else:
            st.session_state.source_name = src_name
            st.session_state.step = 3
            st.rerun()

    if st.button("BACK"):
        st.session_state.step = 1
        st.rerun()

# ========== 3. GENERATE PERSONA ==========
elif step == 3:
    st.markdown('<div class="biglabel">GENERATING YOUR PARENTING AGENT PERSONA</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar">🧠✨</div>', unsafe_allow_html=True)
    for msg in ["Assimilating Knowledge…", "Synthesizing Information…", "Assessing Results…", "Generating Persona…"]:
        st.info(msg)
    st.write("Please wait ~10 s…")

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

    st.info(st.session_state.persona_description)
    if st.button("RETRY"):
        del st.session_state.persona_description
        st.rerun()
    if st.button("SAVE"):
        st.session_state.step = 4
        st.rerun()

# ========== 4. PROFILE DETAILS ==========
elif step == 4:
    st.markdown('<div class="biglabel">PARENTING AGENT DETAILS</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar">📷</div>', unsafe_allow_html=True)
    with st.form("profile"):
        p_name  = st.text_input("Parent first name")
        c_age   = st.number_input("Child age", 1, 21)
        c_name  = st.text_input("Child first name")
        prof_nm = st.text_input("Profile name")
        saved   = st.form_submit_button("SAVE")
    if saved:
        if not all([p_name,c_age,c_name,prof_nm]):
            st.warning("Please fill every field.")
        else:
            profile = PersonaProfile(
                profile_name=prof_nm,parent_name=p_name,child_name=c_name,child_age=int(c_age),
                source_type=st.session_state.source_type,source_name=st.session_state.source_name,
                persona_description=st.session_state.persona_description
            )
            st.session_state.profiles.append(profile.dict())
            save_json(PROFILES_FILE, st.session_state.profiles)
            st.success("Profile saved!")
            st.session_state.step = 5
            st.rerun()
    if st.button("BACK"):
        st.session_state.step = 3
        st.rerun()

# ========== 5. PROFILE CREATED ==========
elif step == 5:
    st.markdown('<div class="biglabel">PARENTING AGENT PROFILE CREATED! 🎉</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar">📝🎉</div>', unsafe_allow_html=True)
    if st.button("CREATE ANOTHER"):
        [st.session_state.pop(k,None) for k in ["source_type","source_name","persona_description"]]
        st.session_state.step=1
        st.rerun()
    if st.button("CHAT"):
        st.session_state.step = 6
        st.rerun()
    if st.button("HOME"):
        st.session_state.step=0
        st.rerun()

# ========== 6. CHAT ==========
elif step == 6:
    # ——— Header ———
    st.markdown('<div class="biglabel">1. SELECT A PARENTING AGENT</div>', unsafe_allow_html=True)

    # ——— Profile selector & info container with hover tooltip ———
    
    # ─── Dropdown + tooltip icon ───
    names = [p["profile_name"] for p in st.session_state.profiles]
    col_dd, col_icon = st.columns([4, 1])
    idx = col_dd.selectbox(
        "Parenting Agent Profiles:",
        range(len(names)),
        format_func=lambda i: names[i],
        key="chat_profile"
    )
    sel = st.session_state.profiles[idx]

    # build tooltip text with newlines
    tooltip = (
        f"Profile: {sel['profile_name']} "
        f"Type: {sel['source_type']} "
        f"Source: {sel['source_name']} "
        f"Child: {sel['child_name']} "
        f"Age: {sel['child_age']} "
        f"Parent: {sel['parent_name']} "
        f"Persona: {sel['persona_description']}"
    )
    # render info icon with hover title
    col_icon.markdown(
        f"""<span title="{tooltip}" style="font-size:1.5em; cursor:help;">ℹ️</span>""",
        unsafe_allow_html=True,
    )
    
    # ─── Active‐profile info bar (with light background + label) ───
    st.markdown(
        f"""
        <div style="
            background: #d3d3d3;         /* light grey */
            padding: 12px;              /* inner spacing */
            border-radius: 8px;         /* rounded corners */
            margin-top: 12px;
        ">
          <!-- Static header label -->
          <div style="width:100%; margin-bottom:8px;">
            <span style="color:#27e67a; font-weight:700; font-size:1.2em;">ACTIVE AGENT</span>
          </div>

          <!-- Profile fields -->
          <div style="
              display: flex;
              justify-content: space-between;
              align-items: center;
              flex-wrap: wrap;
          ">
            <div style="margin:4px 0;">
              <span style="color:#27e67a; font-weight:600;">Profile:</span>
              <span style="color:#000000; font-weight:500;">{sel['profile_name']}</span>
            </div>
            <div style="margin:4px 0;">
              <span style="color:#27e67a; font-weight:600;">Source:</span>
              <span style="color:#000000; font-weight:500;">{sel['source_name']}</span>
            </div>
            <div style="margin:4px 0;">
              <span style="color:#27e67a; font-weight:600;">Child Age:</span>
              <span style="color:#000000; font-weight:500;">{sel['child_age']}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # close the container
    st.markdown("</div>", unsafe_allow_html=True)


    # ——— Static buttons for response shortcuts ———
    st.markdown('<div class="biglabel">2. SELECT A RESPONSE TYPE</div>', unsafe_allow_html=True)

    # ensure there's always a default in state
    st.session_state.setdefault("shortcut", "💬 DEFAULT")

    # ——— Static buttons for response shortcuts (emoji + detailed tooltip) ———
    SHORTCUTS = ["💬 DEFAULT", "🤝 CONNECT", "🌱 GROW", "🔍 EXPLORE", "🛠 RESOLVE", "❤ SUPPORT"]
    EMOJIS = {
        "💬 DEFAULT": "💬",
        "🤝 CONNECT": "🤝",
        "🌱 GROW": "🌱",
        "🔍 EXPLORE": "🔍",
        "🛠 RESOLVE": "🛠",
        "❤ SUPPORT": "❤",
    }
    TOOLTIPS = {
        "💬 DEFAULT": "💬 DEFAULT - No formatting",
        "🤝 CONNECT": "🤝 CONNECT – Help you explain complex ideas to your child with three clear examples.",
        "🌱 GROW":    "🌱 GROW – Strategies to improve your parenting skills.",
        "🔍 EXPLORE": "🔍 EXPLORE – Start a Q&A session with age-appropriate explanations.",
        "🛠 RESOLVE": "🛠 RESOLVE – Step-by-step advice to tackle your parenting challenge.",
        "❤ SUPPORT": "❤ SUPPORT – Empathetic guidance and 2–3 practical tips.",
    }

    cols = st.columns(len(SHORTCUTS))
    for i, sc in enumerate(SHORTCUTS):
        emoji = EMOJIS[sc]
        with cols[i]:
            if st.button(emoji, key=f"type_{sc}", help=TOOLTIPS[sc]):
                st.session_state.shortcut = sc

    # ——— Selected-response indicator (white box) ———
    st.markdown(
        f"""
        <div style="
            background:#ffffff;
            color:#000000;
            padding:12px;
            border-radius:8px;
            margin-top:12px;
            margin-bottom:12px;
        ">
          <strong>Selected:</strong> {st.session_state.shortcut}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ——— Query Title ———
    st.markdown('<div class="biglabel">3. WHAT DO YOU WANT TO ASK?</div>', unsafe_allow_html=True)

    # ——— Query input & send ———
    query = st.text_area("Type here", key="chat_query")

    # last answer bubble
    if st.session_state.last_answer:
        st.markdown(
            f"<div class='answer-box'>{st.session_state.last_answer}</div>",
            unsafe_allow_html=True
        )
    if st.button("SEND", key="send_btn"):
        # build the system prompt
        base = (
            f"You are a parenting coach with this persona: {sel['persona_description']}."
            f" Parent: {sel['parent_name']}, Child: {sel['child_name']}, Age: {sel['child_age']}."
        )
        extra = {
            "🤝 CONNECT": " Help the parent explain complex ideas to the child. Give three examples.",
            "🌱 GROW":    " Offer three advanced strategies for parenting skill improvement.",
            "🔍 EXPLORE": " Facilitate a Q&A session with age-appropriate explanations.",
            "🛠 RESOLVE": " Provide step-by-step resolution advice.",
            "❤ SUPPORT": " Offer empathetic support and 2-3 pieces of advice."
        }.get(st.session_state.shortcut, "")
        prompt = base + extra + "\n" + query + "\nRespond as a JSON object with 'answer'."
        
        # call the new 1.0+ client
        out = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":prompt}],
            response_format={"type":"json_object"}
        )

        # extract and parse the JSON response
        raw = out.choices[0].message.content
        st.session_state.last_answer = json.loads(raw)["answer"]

        # re-run to display answer
        st.rerun()


    # ——— Navigation buttons ———
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("SAVE RESPONSE", key="save_response"):
            record = {
                "profile":  sel["profile_name"],
                "shortcut": st.session_state.shortcut,
                "question": query,
                "answer":   st.session_state.last_answer
            }
            if record not in st.session_state.saved_responses:
                st.session_state.saved_responses.append(record)
                save_json(RESPONSES_FILE, st.session_state.saved_responses)
            st.session_state.step = 7
            st.rerun()
    with nav_col2:
        if st.button("SAVED RESPONSES", key="chat_saved"):
            if st.session_state.saved_responses:
                st.session_state.step = 7
                st.rerun()
            else:
                st.warning("No saved responses yet.")

    if st.button("Back to Profiles", key="chat_back"):
        st.session_state.step = 5
        st.rerun()

# ========== 7. SAVED RESPONSES ==========
elif step == 7:
    st.markdown('<div class="biglabel">SELECT A SAVED CHAT</div>', unsafe_allow_html=True)
    
    if not st.session_state.saved_responses:
        st.info("No saved responses."); st.session_state.step=0; st.rerun()

    titles = [f"{i+1}. {r['profile']} – {r['shortcut']}" for i,r in enumerate(st.session_state.saved_responses)]
    sel_idx = st.selectbox("Saved ChatS:", range(len(titles)), format_func=lambda i: titles[i])
    item = st.session_state.saved_responses[sel_idx]

   # ─── Styled Saved Response details ───
    st.markdown(
        f'''
        <p style="color:#ffffff; margin:4px 0;">
          <strong>Profile:</strong> {item["profile"]}
        </p>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''
        <p style="color:#ffffff; margin:4px 0;">
          <strong>Shortcut:</strong> {item["shortcut"]}
        </p>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(
        '''
        <p style="color:#ffffff; margin:4px 0;">
          <strong>Question:</strong>
        </p>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''
        <blockquote style="
            color:#ffffff;
            border-left: 4px solid #27e67a;
            padding-left: 8px;
            margin: 4px 0;
        ">
          {item["question"]}
        </blockquote>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(
        '''
        <p style="color:#ffffff; margin:4px 0;">
          <strong>Answer:</strong>
        </p>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''
        <div class="answer-box" style="color:#ffffff;">
          {item["answer"]}
        </div>
        ''',
        unsafe_allow_html=True,
    )


    if st.button("DELETE"):
        st.session_state.saved_responses.pop(sel_idx)
        save_json(RESPONSES_FILE, st.session_state.saved_responses)
        st.rerun()
    if st.button("CLOSE"): st.session_state.step = 0; st.rerun()

# ========== 8. PROFILE MANAGER ==========
elif step == 8:
    st.markdown('<div class="biglabel">MY PROFILES</div>', unsafe_allow_html=True)
    st.markdown('<div class="frame-avatar">🗂️</div>', unsafe_allow_html=True)

    if not st.session_state.profiles:
        st.info("No profiles stored."); st.session_state.step = 0; st.rerun()

    titles = [f"{i+1}. {p['profile_name']}" for i,p in enumerate(st.session_state.profiles)]
    idx = st.selectbox("Select a profile to view / edit", range(len(titles)), format_func=lambda i: titles[i])
    prof = st.session_state.profiles[idx]

    with st.form("edit_profile"):
        p_name = st.text_input("Parent first name", value=prof["parent_name"])
        c_age  = st.number_input("Child age", 1, 21, value=prof["child_age"])
        c_name = st.text_input("Child first name", value=prof["child_name"])
        src_t  = st.text_input("Source type (display)", value=prof["source_type"], disabled=True)
        src_n  = st.text_input("Source name (display)", value=prof["source_name"], disabled=True)
        prof_nm= st.text_input("Profile name", value=prof["profile_name"])
        desc   = st.text_area("Persona description", value=prof["persona_description"], height=150)
        saved  = st.form_submit_button("SAVE CHANGES")
    if saved:
        prof.update(parent_name=p_name, child_age=int(c_age), child_name=c_name,
                    profile_name=prof_nm, persona_description=desc)
        st.session_state.profiles[idx] = prof
        save_json(PROFILES_FILE, st.session_state.profiles)
        st.success("Profile updated!")

    col1,col2 = st.columns(2)
    if col1.button("DELETE PROFILE"):
        st.session_state.profiles.pop(idx)
        save_json(PROFILES_FILE, st.session_state.profiles)
        st.experimental_rerun()
    if col2.button("CLOSE"):
        st.session_state.step = 0; st.rerun()
