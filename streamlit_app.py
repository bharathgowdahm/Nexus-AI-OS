"""
NEXUS AI OS - GEMINI 3.8 ULTRA - FINAL ULTRA
- Uses direct Google REST API (no lib needed) + OpenAI compatible endpoint
- Models: gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-pro
- 3.8 Ultra = Gemini 2.5 Pro thinking mode
"""
import streamlit as st
import os
import requests
import json

st.set_page_config(page_title="NEXUS AI OS - Gemini 3.8 Ultra", page_icon="🧠", layout="wide")

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
MODEL = "gemini-2.5-flash-preview-05-20 (Ultra 3.8)"

def call_gemini_direct_rest(system_prompt, user_prompt, api_key):
    """Direct REST call - most reliable, no library"""
    url_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    
    models = [
        "gemini-2.5-flash-preview-05-20",
        "gemini-2.5-pro-preview-05-06",
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro"
    ]
    
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 3000}
    }
    
    for model in models:
        try:
            url = url_template.format(model=model, key=api_key)
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                # Parse response
                if "candidates" in data and len(data["candidates"]) > 0:
                    cand = data["candidates"][0]
                    if "content" in cand and "parts" in cand["content"]:
                        text = cand["content"]["parts"][0].get("text","")
                        if text:
                            return text
            # If 404 try next model
            if resp.status_code == 404:
                continue
        except Exception as e:
            continue
    return None

def call_gemini_openai_fallback(system_prompt, user_prompt, api_key):
    """OpenAI compatible fallback"""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        for m in ["gemini-2.5-flash-preview-05-20", "gemini-2.5-pro-preview-05-06", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                resp = client.chat.completions.create(
                    model=m,
                    messages=[
                        {"role":"system","content":system_prompt},
                        {"role":"user","content":user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=3000
                )
                return resp.choices[0].message.content
            except:
                continue
    except Exception as e:
        pass
    return None

def call_gemini(system_prompt, user_prompt):
    if not api_key:
        return "❌ Add GOOGLE_API_KEY in Streamlit Secrets. Get FREE from https://aistudio.google.com/app/apikey"
    
    # Try 1: Direct REST (most stable)
    result = call_gemini_direct_rest(system_prompt, user_prompt, api_key)
    if result:
        return result
    
    # Try 2: OpenAI fallback
    result = call_gemini_openai_fallback(system_prompt, user_prompt, api_key)
    if result:
        return result
    
    return "❌ Gemini failed. Check: 1) GOOGLE_API_KEY valid? 2) Quota? Get new key from https://aistudio.google.com/app/apikey and add in Secrets, then Reboot."

class AgentOrchestrator:
    def planner(self, task):
        return call_gemini("You are NEXUS Ultra Planner - Gemini 3.8. Break tasks into 4 elite steps with tech stack, architecture, security.", f"Plan: {task}")
    def researcher(self, task):
        return call_gemini("You are NEXUS Researcher Ultra. Find best libraries, patterns, performance tips.", f"Research: {task}")
    def coder(self, task, research):
        return call_gemini("You are senior Staff Engineer (Google level). Generate PRODUCTION-READY Python code with FastAPI, type hints, docstrings, error handling, tests. Return ONLY python code in ```python block.", f"Task: {task}\nResearch: {research}\nGenerate ULTRA code:")
    def critic(self, code):
        return call_gemini("You are Principal Engineer Critic. Review security, bugs, performance. Score /100 with fixes.", f"Review:\n{code[:5000]}")

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
    st.title("🧠 NEXUS 3.8 ULTRA")
    st.caption(f"Gemini 3.8 Ultra • {MODEL}")
    if api_key:
        st.success(f"🟢 Gemini ULTRA Connected\n3.8 Ultra\nKey: {api_key[:12]}...")
    else:
        st.warning("🟡 Mock Mode")
        st.markdown("[Get FREE Gemini Key](https://aistudio.google.com/app/apikey)")
        st.info("Add in: Manage app → Settings → Secrets\nGOOGLE_API_KEY = \"AI...\"")
    st.divider()
    st.subheader("📚 Second Brain")
    uploaded = st.file_uploader("Upload .txt/.py/.md", type=["txt","py","md"])
    if uploaded:
        content = uploaded.read().decode("utf-8", errors="ignore")[:10000]
        st.session_state.rag_docs.append({"name": uploaded.name, "content": content})
        st.success(f"Indexed: {uploaded.name} | Total: {len(st.session_state.rag_docs)}")
    st.caption("Built by Bharath | Ultra Edition")

st.title("What should NEXUS 3.8 ULTRA build today?")
st.caption("Model: Gemini 2.5 Pro Ultra Thinking • Planner → Researcher → Coder → Critic • 100% FREE")

prompt = st.text_area("Prompt", placeholder="e.g. Build a Bingo game with multiplayer, animations, sound...", height=120)
col1, col2 = st.columns([1,4])
with col1:
    run = st.button("🚀 Generate ULTRA", type="primary", use_container_width=True)
with col2:
    clear = st.button("Clear History")
if clear:
    st.session_state.history = []
    st.rerun()

def run_agents(task: str):
    results = simple_search(task, st.session_state.rag_docs)
    rag_ctx = "\n".join([r["content"][:500] for r in results])
    with st.status("🤖 NEXUS ULTRA Swarm Working...", expanded=True) as status:
        st.write("🧠 Ultra Planner (Gemini 3.8 thinking)...")
        plan = orchestrator.planner(task)
        st.write(plan)
        st.write("🔍 Researcher Ultra...")
        research = orchestrator.researcher(task)
        st.write(research)
        st.write("💻 Coder Ultra (Staff level)...")
        code = orchestrator.coder(task, research + "\n" + rag_ctx)
        st.write("✅ Principal Critic...")
        critique = orchestrator.critic(code)
        status.update(label="✅ ULTRA Done!", state="complete", expanded=False)
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
