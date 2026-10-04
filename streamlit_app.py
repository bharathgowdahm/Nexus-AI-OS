"""
NEXUS 3.8 ULTRA - PURE GOOGLE - NO GROQ NEEDED
Only needs GOOGLE_API_KEY starting with AIza...
"""
import streamlit as st
import os
import requests

st.set_page_config(page_title="NEXUS 3.8 ULTRA - Google Only", page_icon="🧠", layout="wide")

def get_google_key():
    k = ""
    try:
        k = st.secrets.get("GOOGLE_API_KEY","") or st.secrets.get("GEMINI_API_KEY","")
    except:
        pass
    return k or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""

google_key = get_google_key()
MODEL = "gemini-2.5-flash (Google Only)"

def call_gemini_rest(system_prompt, user_prompt, api_key):
    url_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    models = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-preview-05-20",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro"
    ]
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 3000}
    }
    last_error = "no call"
    for model in models:
        try:
            url = url_template.format(model=model, key=api_key)
            resp = requests.post(url, json=payload, timeout=30)
            last_error = f"Model {model}: HTTP {resp.status_code} - {resp.text[:400]}"
            if resp.status_code == 200:
                data = resp.json()
                if "candidates" in data and data["candidates"]:
                    txt = data["candidates"][0].get("content",{}).get("parts",[{}])[0].get("text","")
                    if txt:
                        return txt, f"Success with {model}"
        except Exception as e:
            last_error = f"Exception with {model}: {e}"
            continue
    return None, last_error

def call_gemini(system_prompt, user_prompt):
    if not google_key:
        return "❌ No GOOGLE_API_KEY found. Add in Secrets: GOOGLE_API_KEY = 'AIza...' from https://aistudio.google.com/app/apikey"
    
    if google_key.startswith("AQ."):
        return f"""❌ WRONG KEY FORMAT!

Your key: {google_key[:20]}... (starts with AQ.)

This is an OAuth access token, NOT a Gemini API key. Gemini API will REJECT it.

=== HOW TO GET CORRECT GOOGLE KEY (30 seconds) ===

1. Open this link on your phone/computer:
   https://aistudio.google.com/app/apikey

2. You will see a page "API keys" with a blue button "Create API key"

3. Click "Create API key" -> Choose "Create API key in new project" (or select existing project)

4. A popup shows a key like: AIzaSyD-xxxx... (39 characters, starts with AIza)

5. Click COPY icon next to the key

6. Go to your Streamlit app:
   xom.streamlit.app -> Manage app (bottom right) -> Settings -> Secrets

7. DELETE your old key and paste:
   GOOGLE_API_KEY = "AIzaSy...your_new_key"

8. Click Save -> It will Reboot automatically -> Then try again!

Your current AQ. key will NEVER work for Gemini. You MUST get AIza... key.
"""

    txt, debug = call_gemini_rest(system_prompt, user_prompt, google_key)
    if txt:
        return txt
    return f"❌ Gemini API failed: {debug}\n\nYour key: {google_key[:15]}... Length: {len(google_key)}\nIf key starts with AIza... and still fails, check quota or create new key at https://aistudio.google.com/app/apikey"

class AgentOrchestrator:
    def planner(self, t): return call_gemini("You are NEXUS Ultra Planner. Break task into 4 clear steps with tech stack.", f"Plan: {t}")
    def researcher(self, t): return call_gemini("You are NEXUS Researcher. Best practices, libraries.", f"Research: {t}")
    def coder(self, t, r): return call_gemini("You are senior Staff Engineer. Generate PRODUCTION-READY Python code. Return ONLY python code in ```python block.", f"Task: {t}\nResearch: {r}")
    def critic(self, c): return call_gemini("You are Principal Critic. Review, score /100.", f"Review:\n{c[:5000]}")

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
    st.caption("Pure Google • No Groq Needed")
    
    if google_key:
        if google_key.startswith("AQ."):
            st.error(f"❌ WRONG KEY!\n{google_key[:18]}...\nAQ. = OAuth token, NOT API key!\nYou need AIza... key")
            st.markdown("### 📸 Step-by-Step:")
            st.markdown("**1.** Go to:")
            st.markdown("`https://aistudio.google.com/app/apikey`")
            st.markdown("**2.** Click **Create API Key** (blue button)")
            st.markdown("**3.** Copy key `AIzaSy...`")
            st.markdown("**4.** Streamlit Secrets: Replace `GOOGLE_API_KEY`")
            st.markdown("**5.** Save → Reboot")
        elif google_key.startswith("AIza"):
            st.success(f"✅ CORRECT KEY FORMAT!\n🟢 Gemini Ready\n{google_key[:12]}...\nLength: {len(google_key)}")
            st.balloons()
        else:
            st.warning(f"Unknown format: {google_key[:12]}... Length {len(google_key)}")
    else:
        st.warning("🟡 No GOOGLE_API_KEY in Secrets")
        st.markdown("Get from https://aistudio.google.com/app/apikey")
        st.code('GOOGLE_API_KEY = "AIzaSy..."', language="toml")

    st.divider()
    st.subheader("📚 Memory")
    up = st.file_uploader("Upload .txt/.py/.md", type=["txt","py","md"])
    if up:
        content = up.read().decode("utf-8", errors="ignore")[:10000]
        st.session_state.rag_docs.append({"name": up.name, "content": content})
        st.success(f"Indexed: {up.name}")

st.title("What should NEXUS 3.8 ULTRA build today?")
st.caption("Pure Google Gemini • No Groq Needed • 100% FREE")

# Show big warning if key wrong
if google_key and google_key.startswith("AQ."):
    st.error("### ❌ Your GOOGLE_API_KEY is WRONG! It starts with AQ. (OAuth token)")
    st.warning("Gemini needs key starting with AIza... Get correct key from https://aistudio.google.com/app/apikey")
    st.info("Watch: Your key AQ.Ab8RN6... will NEVER work. You must replace with AIza... key in Secrets and Reboot.")

prompt = st.text_area("Prompt", placeholder="e.g. Build a Bingo game in Python...", height=120)
c1,c2 = st.columns([1,4])
with c1: run = st.button("🚀 Generate with Google", type="primary", use_container_width=True)
with c2: clear = st.button("Clear")
if clear: st.session_state.history=[]; st.rerun()

def run_agents(task):
    results = simple_search(task, st.session_state.rag_docs)
    rag_ctx = "\n".join([r["content"][:500] for r in results])
    with st.status("🤖 NEXUS Google Working...", expanded=True) as s:
        s.write("🧠 Planner (Google Gemini)...")
        plan = orch.planner(task); s.write(plan)
        s.write("🔍 Researcher...")
        res = orch.researcher(task); s.write(res)
        s.write("💻 Coder (Staff)...")
        code = orch.coder(task, res+"\n"+rag_ctx)
        s.write("✅ Critic...")
        crit = orch.critic(code)
        s.update(label="✅ Done!", state="complete", expanded=False)
    return plan,res,code,crit

if run and prompt:
    if google_key and google_key.startswith("AQ."):
        st.error("Stop! Fix your key first. See sidebar. Your AQ. key will never work.")
    else:
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
