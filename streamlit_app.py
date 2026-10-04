"""
NEXUS AI OS - GEMINI FREE - FINAL WORKING v5
Bug free - uses only openai library
"""
import streamlit as st
import os

st.set_page_config(page_title="NEXUS AI OS - Gemini FREE", page_icon="🧠", layout="wide")

def get_api_key():
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except:
        pass
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""

api_key = get_api_key()
MODEL = "gemini-2.5-flash"

def call_gemini(system_prompt, user_prompt):
    if not api_key:
        return "Add GOOGLE_API_KEY from https://aistudio.google.com/app/apikey"
    last_err = "no attempt yet"
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        for m in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"]:
            try:
                resp = client.chat.completions.create(
                    model=m,
                    messages=[
                        {"role":"system","content":system_prompt},
                        {"role":"user","content":user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2500
                )
                text = resp.choices[0].message.content
                if text:
                    return text
            except Exception as e:
                last_err = str(e)
                continue
        return f"Error: All Gemini models failed. Last error: {last_err}. Check if GOOGLE_API_KEY is valid and has free quota."
    except Exception as e:
        return f"Error: {e} | Last: {last_err}"

class AgentOrchestrator:
    def planner(self, task):
        return call_gemini("You are NEXUS Planner Agent. Break tasks into 3-4 clear steps with tech stack.", f"Plan: {task}")
    def researcher(self, task):
        return call_gemini("You are Researcher Agent. Find best practices, libraries.", f"Research: {task}")
    def coder(self, task, research):
        return call_gemini("You are senior Python engineer. Generate PRODUCTION-READY Python code. Return ONLY code in python block.", f"Task: {task}\nResearch: {research}")
    def critic(self, code):
        return call_gemini("You are Critic Agent. Review code for security & quality. Score /100.", f"Review:\n{code[:4000]}")

if "rag_docs" not in st.session_state:
    st.session_state.rag_docs = []
    st.session_state.history = []
    st.session_state.orchestrator = AgentOrchestrator()

def simple_search(query, docs, k=3):
    q = query.lower()
    scored = [(sum(1 for w in q.split() if w in d["content"].lower()), d) for d in docs]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [d for s,d in scored[:k] if s>0]

orchestrator = st.session_state.orchestrator

with st.sidebar:
    st.title("🧠 NEXUS")
    st.caption(f"Gemini FREE • {MODEL}")
    if api_key:
        st.success(f"🟢 Gemini FREE Connected\n{MODEL}\nKey: {api_key[:15]}...")
    else:
        st.warning("🟡 Mock Mode - Add GOOGLE_API_KEY")
        st.markdown("[Get FREE key](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.subheader("📚 Memory")
    uploaded = st.file_uploader("Upload .txt/.py/.md", type=["txt","py","md"])
    if uploaded:
        content = uploaded.read().decode("utf-8", errors="ignore")[:10000]
        st.session_state.rag_docs.append({"name": uploaded.name, "content": content})
        st.success(f"Indexed: {uploaded.name}")

st.title("What should NEXUS build today?")
st.caption(f"Model: {MODEL} • Planner → Researcher → Coder → Critic • Gemini FREE")
prompt = st.text_area("Prompt", placeholder="e.g. Build a Bingo game in Python...", height=120)
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
    with st.status("🤖 Working with Gemini...", expanded=True) as status:
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
