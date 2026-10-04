"""
NEXUS AI OS - Single File Standalone for Streamlit Cloud
Works with ONLY: streamlit, openai, python-dotenv
No external folders needed - fixes ModuleNotFoundError
"""
import streamlit as st
import os, asyncio
from openai import AsyncOpenAI

st.set_page_config(
    page_title="NEXUS AI OS",
    page_icon="🧠",
    layout="wide"
)

# --- API KEY from Streamlit Secrets or .env ---
def get_api_key():
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except:
        pass
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    return os.getenv("OPENAI_API_KEY", "")

api_key = get_api_key()

# --- Orchestrator built-in ---
class AgentOrchestrator:
    def __init__(self, api_key=""):
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = "gpt-4o-mini"

    async def _call(self, system, user):
        if not self.client:
            return f"[MOCK MODE - Add OPENAI_API_KEY in Secrets]\nSystem: {system[:80]}\nTask: {user[:300]}...\n\n(Add your key in Streamlit Cloud → Manage app → Settings → Secrets to get real AI output)"
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role":"system","content":system},{"role":"user","content":user}],
                temperature=0.7,
                max_tokens=1500
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"

    async def planner(self, task):
        return await self._call("You are NEXUS Planner Agent. Break tasks into 3-4 clear professional steps.", f"Plan: {task}")
    async def researcher(self, task):
        return await self._call("You are Researcher Agent. Find best practices, libraries.", f"Research: {task}")
    async def coder(self, task, research):
        return await self._call("You are senior Python engineer. Generate PRODUCTION-READY Python code with FastAPI, type hints, docstrings. Return ONLY code in ```python block.", f"Task: {task}\nResearch: {research}\nGenerate code:")
    async def critic(self, code):
        return await self._call("You are Critic Agent. Review for security & quality. Score /100.", f"Review:\n{code[:3000]}")

# --- Memory ---
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
    st.caption("Autonomous AI OS v1.0")
    if api_key:
        st.success("🟢 OpenAI Connected")
    else:
        st.warning("🟡 Mock Mode")
        st.info('Add Secret:\nOPENAI_API_KEY = "sk-proj-..."')
    st.divider()
    st.subheader("📚 Memory")
    uploaded = st.file_uploader("Upload .txt/.py/.md", type=["txt","py","md"])
    if uploaded:
        content = uploaded.read().decode("utf-8", errors="ignore")[:10000]
        st.session_state.rag_docs.append({"name": uploaded.name, "content": content})
        st.success(f"Indexed: {uploaded.name} | Total: {len(st.session_state.rag_docs)}")
    st.caption("Built by Bharath | 2026 Trending")

st.title("What should NEXUS build today?")
st.caption("Planner → Researcher → Coder → Critic swarm • Pure Python")

prompt = st.text_area("Prompt", placeholder="e.g. Build a FastAPI todo API with JWT auth, SQLAlchemy, and pytest...", height=120)
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
