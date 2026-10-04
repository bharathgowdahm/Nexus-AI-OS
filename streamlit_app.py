
"""
NEXUS AI OS - GEMINI FREE EDITION - FIXED v3
Uses google-generativeai official SDK - works with all new models
Models: gemini-2.5-flash (latest), gemini-2.0-flash, gemini-1.5-flash
"""
import streamlit as st
import os

st.set_page_config(page_title="NEXUS AI OS - Gemini FREE", page_icon="🧠", layout="wide")

def get_api_key():
    api_key = ""
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
        elif "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except:
        pass
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    except:
        pass
    return api_key

api_key = get_api_key()
MODEL = "gemini-2.5-flash"  # Latest stable free model 2026

def call_gemini(system_prompt, user_prompt, model_name=MODEL):
    if not api_key:
        return "[MOCK MODE - Add GOOGLE_API_KEY]\nGet from https://aistudio.google.com/app/apikey"
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Try models in order: 2.5-flash -> 2.0-flash -> 1.5-flash
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro"
        ]
        
        last_error = ""
        for m in models_to_try:
            try:
                model = genai.GenerativeModel(m, system_instruction=system_prompt)
                response = model.generate_content(user_prompt)
                return response.text
            except Exception as e:
                last_error = str(e)
                if "404" in last_error or "not found" in last_error.lower() or "not supported" in last_error.lower():
                    continue
                # If other error, break
                if "quota" in last_error.lower() or "429" in last_error:
                    return f"Quota exceeded: {last_error} - wait 1 min or create new key"
                continue
        return f"Error: All models failed. Last: {last_error}"
    except Exception as e:
        return f"Error: {e}"

class AgentOrchestrator:
    def __init__(self, api_key=""):
        self.api_key = api_key

    def planner(self, task):
        return call_gemini("You are NEXUS Planner Agent. Break tasks into 3-4 clear steps with tech stack.", f"Plan: {task}")

    def researcher(self, task):
        return call_gemini("You are Researcher Agent. Find best practices, libraries, architecture.", f"Research: {task}")

    def coder(self, task, research):
        return call_gemini("You are senior Python engineer. Generate PRODUCTION-READY Python code with FastAPI, type hints, docstrings, error handling. Return ONLY code in python block.", f"Task: {task}\nResearch: {research}\nGenerate code:")

    def critic(self, code):
        return call_gemini("You are Critic Agent. Review for security, bugs, performance. Score /100 and suggest fixes.", f"Review:\n{code[:4000]}")

if "rag_docs" not in st.session_state:
    st.session_state.rag_docs = []
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator(api_key=api_key)
    st.session_state.history = []

def simple_search(query, docs, k=3):
    q = query.lower()
    scored = []
    for d in docs:
        score = sum(1 for w in q.split() if w in d["content"].lower())
        scored.append((score, d))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [d for s,d in scored[:k] if s>0]

orchestrator = st.session_state.orchestrator

with st.sidebar:
    st.title("🧠 NEXUS")
    st.caption(f"Gemini FREE • {MODEL}")
    if api_key:
        st.success(f"🟢 Gemini FREE Connected\n{MODEL}\nKey: {api_key[:10]}...")
    else:
        st.warning("🟡 Mock Mode")
        st.markdown("""
**Get FREE Gemini Key:**

**Link:** [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

1. Login → Create API Key
2. Copy `AI...`
3. Streamlit → Manage app → Settings → Secrets:
```
GOOGLE_API_KEY = "AI..."
```
""")
    st.divider()
    st.subheader("📚 Memory")
    uploaded = st.file_uploader("Upload .txt/.py/.md", type=["txt","py","md"])
    if uploaded:
        content = uploaded.read().decode("utf-8", errors="ignore")[:10000]
        st.session_state.rag_docs.append({"name": uploaded.name, "content": content})
        st.success(f"Indexed: {uploaded.name} | Total: {len(st.session_state.rag_docs)}")
    st.caption("Built by Bharath | Gemini Free")

st.title("What should NEXUS build today?")
st.caption(f"Model: {MODEL} • Planner → Researcher → Coder → Critic • Gemini FREE")

prompt = st.text_area("Prompt", placeholder="e.g. Build a FastAPI todo API with JWT auth...", height=120)
col1, col2 = st.columns([1,4])
with col1:
    run = st.button("🚀 Generate with Gemini", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear")

if clear:
    st.session_state.history = []
    st.rerun()

def run_agents(task: str):
    results = simple_search(task, st.session_state.rag_docs)
    rag_ctx = "\n".join([r["content"][:500] for r in results])
    with st.status("🤖 Agent Swarm Working with Gemini...", expanded=True) as status:
        st.write("🧠 Planner...")
        plan = orchestrator.planner(task)
        st.write(plan)
        st.write("🔍 Researcher...")
        research = orchestrator.researcher(task)
        st.write(research)
        st.write("💻 Coder...")
        code = orchestrator.coder(task, research + "\n" + rag_ctx)
        st.write("✅ Critic...")
        critique = orchestrator.critic(code)
        status.update(label="✅ Done!", state="complete", expanded=False)
    return plan, research, code, critique

if run and prompt:
    plan, research, code, critique = run_agents(prompt)
    st.session_state.history.append({"prompt": prompt, "plan": plan, "research": research, "code": code, "critique": critique})
    st.divider()
    st.subheader(f"Result for: {prompt}")
    tab1, tab2, tab3, tab4 = st.tabs(["🧠 Plan", "🔍 Research", "💻 Code", "✅ Review"])
    with tab1: st.markdown(plan)
    with tab2: st.markdown(research)
    with tab3: st.code(code, language="python")
    with tab4: st.markdown(critique)

if st.session_state.history:
    st.divider()
    st.subheader("📜 History")
    for h in reversed(st.session_state.history):
        with st.expander(f"{h['prompt'][:60]}..."):
            st.code(h['code'], language="python")
