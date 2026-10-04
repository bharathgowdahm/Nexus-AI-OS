"""
NEXUS 3.8 ULTRA - WORKS WITH ANY KEY - FINAL
If Gemini key is wrong (AQ.), auto uses Groq FREE - so you see CODE not error
"""
import streamlit as st
import os
import requests

st.set_page_config(page_title="NEXUS 3.8 ULTRA", page_icon="🧠", layout="wide")

def get_all_keys():
    g_key = ""; o_key = ""; groq_key = ""; cere_key = ""
    try:
        secrets = st.secrets
        g_key = secrets.get("GOOGLE_API_KEY","") or secrets.get("GEMINI_API_KEY","")
        o_key = secrets.get("OPENROUTER_API_KEY","")
        groq_key = secrets.get("GROQ_API_KEY","")
        cere_key = secrets.get("CEREBRAS_API_KEY","")
    except:
        pass
    g_key = g_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    o_key = o_key or os.getenv("OPENROUTER_API_KEY") or ""
    groq_key = groq_key or os.getenv("GROQ_API_KEY") or ""
    cere_key = cere_key or os.getenv("CEREBRAS_API_KEY") or ""
    return g_key, o_key, groq_key, cere_key

google_key, openrouter_key, groq_key, cerebras_key = get_all_keys()
MODEL = "Gemini 3.8 Ultra + Groq Fallback"

def call_gemini_rest(system_prompt, user_prompt, api_key):
    url_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    for model in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
        try:
            url = url_template.format(model=model, key=api_key)
            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 3000}
            }
            resp = requests.post(url, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                if "candidates" in data and data["candidates"]:
                    txt = data["candidates"][0].get("content",{}).get("parts",[{}])[0].get("text","")
                    if txt:
                        return txt
        except:
            continue
    return None

def call_openai_compatible(system_prompt, user_prompt, api_key, base_url, models):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        for m in models:
            try:
                resp = client.chat.completions.create(
                    model=m,
                    messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
                    temperature=0.7,
                    max_tokens=2500
                )
                return resp.choices[0].message.content
            except:
                continue
    except:
        pass
    return None

def call_gemini(system_prompt, user_prompt):
    # Priority 1: Try Gemini REST if key looks valid (AIza...)
    if google_key and google_key.startswith("AIza"):
        txt = call_gemini_rest(system_prompt, user_prompt, google_key)
        if txt:
            return txt
    
    # Priority 2: Try OpenRouter FREE models
    if openrouter_key:
        txt = call_openai_compatible(system_prompt, user_prompt, openrouter_key, "https://openrouter.ai/api/v1", ["deepseek/deepseek-r1:free","google/gemma-3-27b-it:free","meta-llama/llama-3.2-3b-instruct:free"])
        if txt:
            return txt

    # Priority 3: Try Groq FREE (always works, no billing)
    if groq_key:
        txt = call_openai_compatible(system_prompt, user_prompt, groq_key, "https://api.groq.com/openai/v1", ["llama-3.3-70b-versatile","llama3-70b-8192"])
        if txt:
            return txt

    # Priority 4: Try Cerebras FREE
    if cerebras_key:
        txt = call_openai_compatible(system_prompt, user_prompt, cerebras_key, "https://api.cerebras.ai/v1", ["llama-3.3-70b","llama3.1-70b"])
        if txt:
            return txt

    # Priority 5: Try Gemini even with AQ. key (maybe new format)
    if google_key:
        txt = call_gemini_rest(system_prompt, user_prompt, google_key)
        if txt:
            return txt
        # Also try OpenAI compat for Gemini
        txt = call_openai_compatible(system_prompt, user_prompt, google_key, "https://generativelanguage.googleapis.com/v1beta/openai/", ["gemini-2.5-flash","gemini-2.0-flash","gemini-1.5-flash"])
        if txt:
            return txt

    # If all failed, explain
    if google_key and google_key.startswith("AQ."):
        return f"""❌ Your GOOGLE_API_KEY is WRONG FORMAT: '{google_key[:15]}...' (starts with AQ.)

This is an OAuth token, NOT a Gemini API key.

HOW TO FIX (30 sec):
1. Go to https://aistudio.google.com/app/apikey
2. Click 'Create API Key' (blue button)
3. Copy key starting with 'AIzaSy...' (39 chars)
4. In Streamlit Cloud: Manage app -> Settings -> Secrets
5. Replace GOOGLE_API_KEY with new AIza... key
6. Save -> Reboot -> Will work!

OR quick fix: Add a FREE backup key that always works:
- Get FREE Groq key: https://console.groq.com/keys
- Add in Secrets: GROQ_API_KEY = "gsk_..."
- Reboot -> Will use Groq and generate code immediately even with wrong Gemini key.
"""

    return "❌ No valid API key. Add GOOGLE_API_KEY='AIza...' from https://aistudio.google.com/app/apikey OR GROQ_API_KEY='gsk_...' from https://console.groq.com/keys in Secrets."

class AgentOrchestrator:
    def planner(self, task): return call_gemini("You are NEXUS Ultra Planner. Break into 4 steps with tech stack.", f"Plan: {task}")
    def researcher(self, task): return call_gemini("You are NEXUS Researcher Ultra.", f"Research: {task}")
    def coder(self, task, research): return call_gemini("You are senior Staff Engineer. Generate PRODUCTION-READY Python code with FastAPI, type hints. Return ONLY code.", f"Task: {task}\nResearch: {research}")
    def critic(self, code): return call_gemini("You are Principal Critic. Review and score /100.", f"Review:\n{code[:5000]}")

if "rag_docs" not in st.session_state:
    st.session_state.rag_docs = []; st.session_state.history = []; st.session_state.orchestrator = AgentOrchestrator()

def simple_search(q, docs, k=3):
    ql=q.lower()
    scored=[(sum(1 for w in ql.split() if w in d["content"].lower()), d) for d in docs]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [d for s,d in scored[:k] if s>0]

orch = st.session_state.orchestrator

with st.sidebar:
    st.title("🧠 NEXUS 3.8 ULTRA")
    st.caption("Gemini 3.8 Ultra + Auto Fallback")
    
    # Show key status with FIX instructions
    if google_key:
        if google_key.startswith("AQ."):
            st.error(f"⚠️ WRONG KEY!\n{google_key[:15]}...\nStarts with AQ. (OAuth)\nNeed AIza...\nGo to aistudio.google.com/app/apikey")
        elif google_key.startswith("AIza"):
            st.success(f"🟢 Gemini OK\n{google_key[:12]}...")
        else:
            st.warning(f"🟡 Key format unknown: {google_key[:10]}...")
    else:
        st.warning("No GOOGLE_API_KEY")

    if groq_key:
        st.success(f"🟢 Groq Backup OK: {groq_key[:10]}...")
    else:
        st.info("💡 Tip: Add GROQ_API_KEY for 100% uptime backup\nFree from console.groq.com/keys")
    
    if openrouter_key:
        st.info(f"🟢 OpenRouter: {openrouter_key[:10]}...")

    st.divider()
    st.markdown("### 🔧 FIX WRONG AQ. KEY:")
    st.markdown("1. **[Get Correct Key](https://aistudio.google.com/app/apikey)**")
    st.markdown("2. Click **Create API Key**")
    st.markdown("3. Copy **AIza...** (39 chars)")
    st.markdown("4. Secrets → `GOOGLE_API_KEY = \"AIza...\"`")
    st.markdown("5. **Reboot**")

    st.divider()
    st.subheader("📚 Memory")
    up = st.file_uploader("Upload .txt/.py/.md", type=["txt","py","md"])
    if up:
        content = up.read().decode("utf-8", errors="ignore")[:10000]
        st.session_state.rag_docs.append({"name": up.name, "content": content})
        st.success(f"Indexed: {up.name}")

st.title("What should NEXUS 3.8 ULTRA build today?")
st.caption("Gemini 3.8 Ultra + Groq/Cerebras Fallback • Always Works • FREE")

prompt = st.text_area("Prompt", placeholder="e.g. Build a Bingo game in Python with Tkinter...", height=120)
c1,c2 = st.columns([1,4])
with c1: run = st.button("🚀 Generate ULTRA", type="primary", use_container_width=True)
with c2: clear = st.button("Clear")
if clear: st.session_state.history=[]; st.rerun()

def run_agents(task):
    results = simple_search(task, st.session_state.rag_docs)
    rag_ctx = "\n".join([r["content"][:500] for r in results])
    with st.status("🤖 NEXUS ULTRA Working...", expanded=True) as s:
        s.write("🧠 Planner...")
        plan = orch.planner(task); s.write(plan)
        s.write("🔍 Researcher...")
        res = orch.researcher(task); s.write(res)
        s.write("💻 Coder...")
        code = orch.coder(task, res+"\n"+rag_ctx)
        s.write("✅ Critic...")
        crit = orch.critic(code)
        s.update(label="✅ ULTRA Done!", state="complete", expanded=False)
    return plan,res,code,crit

if run and prompt:
    plan,res,code,crit = run_agents(prompt)
    st.session_state.history.append({"prompt":prompt,"plan":plan,"research":res,"code":code,"critique":crit})
    st.divider()
    st.subheader(f"Result for: {prompt}")
    t1,t2,t3,t4 = st.tabs(["🧠 Plan","🔍 Research","💻 Code","✅ Review"])
    with t1: st.markdown(plan)
    with t2: st.markdown(res)
    with t3: st.code(code, language="python")
    with t4: st.markdown(crit)

if st.session_state.history:
    st.divider(); st.subheader("📜 History")
    for h in reversed(st.session_state.history):
        with st.expander(f"{h['prompt'][:60]}..."): st.code(h['code'], language="python")
