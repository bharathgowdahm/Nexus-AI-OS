"""
NEXUS AI OS - Streamlit Cloud FIXED
Works with ONLY: streamlit, openai, python-dotenv
No chromadb, no rag engine
"""
import streamlit as st
import os, asyncio
from nexus_core.orchestrator import AgentOrchestrator

st.set_page_config(
    page_title="NEXUS AI OS",
    page_icon="🧠",
    layout="wide"
)

def get_api_key():
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except:
        pass
    return os.getenv("OPENAI_API_KEY", "")

api_key = get_api_key()

# Simple in-memory docs (no chromadb)
if "rag_docs" not in st.session_state:
    st.session_state.rag_docs = []

def simple_search(query, docs, k=3):
    q = query.lower()
    scored = []
    for d in docs:
        score = sum(1 for w in q.split() if w in d["content"].lower())
        scored.append((score, d))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [d for s,d in scored[:k] if s>0]

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator(api_key_override=api_key)
    st.session_state.history = []

orchestrator = st.session_state.orchestrator

with st.sidebar:
    st.title("🧠 NEXUS")
    st.caption("Autonomous AI OS v1.0")
    if api_key:
        st.success("🟢 OpenAI Connected")
    else:
        st.warning("🟡 Mock Mode")
        st.info('Add Secret: OPENAI_API_KEY = "sk-proj-..."')
    st.divider()
    st.subheader("📚 Memory")
    uploaded = st.file_uploader("Upload .txt/.py/.md", type=["txt","py","md"])
    if uploaded:
        content = uploaded.read().decode("utf-8", errors="ignore")[:10000]
        st.session_state.rag_docs.append({"name": uploaded.name, "content": content})
        st.success(f"Indexed: {uploaded.name} | Total: {len(st.session_state.rag_docs)}")

st.title("What should NEXUS build today?")
st.caption("Planner → Researcher → Coder → Critic swarm")

prompt = st.text_area("Prompt", placeholder="e.g. Build a FastAPI todo API with JWT auth...", height=120)
col1, col2 = st.columns([1,4])
with col1:
    run = st.button("🚀 Generate", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear")

if clear:
    st.session_state.history = []
    st.rerun()

async def run_agents(task: str):
    results = simple_search(task, st.session_state.rag_docs)
    rag_ctx = "\n".join([r["content"][:500] for r in results])
    with st.status("🤖 Agent Swarm Working...", expanded=True) as status:
        st.write("🧠 Planner...")
        plan = await orchestrator.planner(task)
        st.write(plan)
        st.write("🔍 Researcher...")
        research = await orchestrator.researcher(task)
        st.write(research)
        st.write("💻 Coder...")
        code = await orchestrator.coder(task, research + "\n" + rag_ctx)
        st.write("✅ Critic...")
        critique = await orchestrator.critic(code)
        status.update(label="✅ Done!", state="complete", expanded=False)
    return plan, research, code, critique

if run and prompt:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    plan, research, code, critique = loop.run_until_complete(run_agents(prompt))
    st.session_state.history.append({"prompt": prompt, "plan": plan, "research": research, "code": code, "critique": critique})
    st.divider()
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
