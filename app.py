"""
NEXUS AI OS - Streamlit Cloud Edition
Professional, publish-ready, secret-safe
"""
import streamlit as st
import os, asyncio
from nexus_core.orchestrator import AgentOrchestrator
from nexus_core.rag import RAGEngine

st.set_page_config(
    page_title="NEXUS AI OS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIG: Works locally (.env) AND on Streamlit Cloud (Secrets) ---
def get_api_key():
    # 1. Try Streamlit secrets (for cloud)
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except:
        pass
    # 2. Try env variable (for local)
    return os.getenv("OPENAI_API_KEY", "")

api_key = get_api_key()

# --- CSS for pro look ---
st.markdown("""
<style>
    .main { background-color: #0a0a0b; }
    .stButton>button { border-radius: 20px; }
    .agent-card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 16px; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# --- Init ---
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator(api_key_override=api_key)
    st.session_state.rag = RAGEngine()
    st.session_state.history = []

orchestrator = st.session_state.orchestrator
rag_engine = st.session_state.rag

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧠 NEXUS")
    st.caption("Autonomous AI OS v1.0")
    
    if api_key:
        st.success("🟢 OpenAI Connected")
    else:
        st.warning("🟡 Mock Mode - Add API Key")
        st.info("Go to Streamlit Cloud → App → Settings → Secrets and add:\nOPENAI_API_KEY = \"sk-proj-...\"")
    
    st.divider()
    st.subheader("📚 Second Brain (RAG)")
    uploaded = st.file_uploader("Upload docs (.txt, .py, .md)", type=["txt","py","md"])
    if uploaded:
        content = uploaded.read().decode("utf-8", errors="ignore")[:15000]
        doc_id = rag_engine.ingest(content, {"source": uploaded.name})
        st.success(f"Indexed: {uploaded.name} | Total: {rag_engine.count()}")
    
    query = st.text_input("Search memory")
    if query:
        results = rag_engine.search(query, k=3)
        for r in results:
            st.markdown(f"**{r['meta'].get('source','doc')}**\n{r['text'][:200]}...")
    
    st.divider()
    st.caption("Built by Bharath | Trending 2026")

# --- MAIN ---
st.title("What should NEXUS build today?")
st.caption("Complex multi-agent swarm (Planner → Researcher → Coder → Critic) • Simple UI")

prompt = st.text_area("Prompt", placeholder="e.g. Build a FastAPI todo API with JWT auth, SQLAlchemy, and pytest...", height=100)
col1, col2 = st.columns([1,4])
with col1:
    run = st.button("🚀 Generate with Agent Swarm", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear History")

if clear:
    st.session_state.history = []
    st.rerun()

async def run_agents(task: str):
    rag_ctx = ""
    rag_results = rag_engine.search(task, k=3)
    if rag_results:
        rag_ctx = "\n".join([r['text'][:400] for r in rag_results])
    
    with st.status("🤖 Agent Swarm Working...", expanded=True) as status:
        st.write("🧠 **Planner:** Breaking down task...")
        plan = await orchestrator.planner(task)
        st.write(plan)
        
        st.write("🔍 **Researcher:** Finding best practices...")
        research = await orchestrator.researcher(task)
        st.write(research)
        
        st.write("💻 **Coder:** Generating production code...")
        code = await orchestrator.coder(task, research + "\n" + rag_ctx)
        
        st.write("✅ **Critic:** Reviewing...")
        critique = await orchestrator.critic(code)
        status.update(label="✅ Done! Ready to ship", state="complete", expanded=False)
    
    return plan, research, code, critique, len(rag_results)

if run and prompt:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    plan, research, code, critique, rag_count = loop.run_until_complete(run_agents(prompt))
    
    st.session_state.history.append({
        "prompt": prompt,
        "plan": plan,
        "research": research,
        "code": code,
        "critique": critique
    })
    
    st.divider()
    st.subheader(f"Result for: {prompt}")
    tab1, tab2, tab3, tab4 = st.tabs(["🧠 Plan", "🔍 Research", "💻 Code", "✅ Review"])
    with tab1: st.markdown(plan)
    with tab2: st.markdown(research)
    with tab3: st.code(code, language="python")
    with tab4: st.markdown(critique)

# Show history
if st.session_state.history:
    st.divider()
    st.subheader("📜 History")
    for i, h in enumerate(reversed(st.session_state.history)):
        with st.expander(f"{h['prompt'][:60]}..."):
            st.code(h['code'], language="python")
