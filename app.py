"""
NEXUS AI OS - GEMINI FREE EDITION
100% FREE - Uses Google Gemini 2.0 Flash (free tier: 1500 req/day)
No billing, no card needed
"""
import streamlit as st
import os, asyncio
from openai import AsyncOpenAI

st.set_page_config(page_title="NEXUS AI OS - Gemini FREE", page_icon="🧠", layout="wide")

def get_client():
    api_key = ""
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    model = "gemini-2.0-flash"
    
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
        elif "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        elif "GOOGLE_API_KEY" in st.secrets.keys():
            api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass
    
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    
    # Fallback: if user still has OpenRouter/Groq, use it
    if not api_key:
        try:
            if "OPENROUTER_API_KEY" in st.secrets:
                api_key = st.secrets["OPENROUTER_API_KEY"]
                base_url = "https://openrouter.ai/api/v1"
                model = "deepseek/deepseek-r1:free"
            elif "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
                base_url = "https://api.groq.com/openai/v1"
                model = "llama-3.3-70b-versatile"
        except:
            pass
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GROQ_API_KEY") or ""
    except:
        pass
    
    return api_key, base_url, model

api_key, base_url, model_name = get_client()

class AgentOrchestrator:
    def __init__(self, api_key="", base_url=None, model="gemini-2.0-flash"):
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = None
        self.model = model

    async def _call(self, system, user):
        if not self.client:
            return """[MOCK MODE - Add Gemini FREE key]

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key" (FREE, no card)
3. Copy key starting with "AI..."
4. In Streamlit: Manage app -> Settings -> Secrets -> Add:

GOOGLE_API_KEY = "AI...your_key..."

5. Save -> Reboot -> Done!
"""
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role":"system","content":system},
                    {"role":"user","content":user}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return resp.choices[0].message.content
        except Exception as e:
            # If gemini model fails, try gemini-1.5-flash fallback
            try:
                resp = await self.client.chat.completions.create(
                    model="gemini-1.5-flash",
                    messages=[
                        {"role":"system","content":system},
                        {"role":"user","content":user}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                return resp.choices[0].message.content
            except Exception as e2:
                return f"Error: {e2}. Original: {e}. Make sure GOOGLE_API_KEY is correct and from https://aistudio.google.com/app/apikey"

    async def planner(self, task):
        return await self._call("You are NEXUS Planner Agent. Break tasks into 3-4 clear professional steps with tech stack.", f"Plan: {task}")
    async def researcher(self, task):
        return await self._call("You are Researcher Agent. Find best practices, libraries, architecture.", f"Research: {task}")
    async def coder(self, task, research):
        return await self._call("You are senior Python engineer. Generate PRODUCTION-READY Python code with FastAPI, type hints, docstrings, error handling. Return ONLY code in ```python block.", f"Task: {task}\nResearch: {research}\nGenerate code:")
    async def critic(self, code):
        return await self._call("You are Critic Agent. Review for security, bugs, performance. Score /100 and suggest fixes.", f"Review:\n{code[:4000]}")

if "rag_docs" not in st.session_state:
    st.session_state.rag_docs = []
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator(api_key=api_key, base_url=base_url, model=model_name)
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
    st.caption("Gemini FREE Edition • 2.0 Flash")
    if api_key:
        if "AI" in api_key[:3] or "google" in base_url or "generativelanguage" in base_url:
            st.success(f"🟢 Gemini FREE Connected\n{model_name}")
        else:
            st.success(f"🟢 Connected\n{model_name}")
    else:
        st.warning("🟡 Mock Mode")
        st.markdown("""
**Get FREE Gemini API Key:**

**Step 1:** Go to link:
**[aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)**

**Step 2:** 
- Login with Google
- Tap **"Create API Key"**
- Copy key `AI...`

**Step 3:** 
- Streamlit -> Manage app -> Settings -> Secrets
- Paste:
```
GOOGLE_API_KEY = "AI..."
```
- Save -> Reboot
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
st.caption(f"Model: {model_name} • Planner → Researcher → Coder → Critic • Gemini FREE")

prompt = st.text_area("Prompt", placeholder="e.g. Build a FastAPI todo API with JWT auth, SQLAlchemy, and pytest...", height=120)
col1, col2 = st.columns([1,4])
with col1:
    run = st.button("🚀 Generate with Gemini", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear")

if clear:
    st.session_state.history = []
    st.rerun()

async def run_agents(task: str):
    results = simple_search(task, st.session_state.rag_docs)
    rag_ctx = "\n".join([r["content"][:500] for r in results])
    with st.status("🤖 Agent Swarm Working with Gemini...", expanded=True) as status:
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
