import gradio as gr
from nexus_core.orchestrator import AgentOrchestrator
from nexus_core.rag import RAGEngine
from nexus_core.config import OPENAI_API_KEY
import os

orchestrator = AgentOrchestrator()
rag_engine = RAGEngine()

api_status = "🟢 Real OpenAI Connected" if OPENAI_API_KEY else "🟡 Mock Mode (Add API Key in .env)"

async def handle_task(prompt: str, history):
    if not prompt.strip():
        return history, ""
    history = history + [(prompt, f"🧠 **Planner (GPT-4o-mini):** Thinking...")]
    yield history, ""
    
    # Get RAG context
    rag_ctx = ""
    rag_results = rag_engine.search(prompt, k=3)
    if rag_results:
        rag_ctx = "\n".join([r['text'][:400] for r in rag_results])
    
    plan = await orchestrator.planner(prompt)
    history[-1] = (prompt, f"### 🧠 Plan\n{plan}\n\n---\n🔍 **Researcher:** Searching best practices...")
    yield history, ""
    
    research = await orchestrator.researcher(prompt + f"\nContext: {rag_ctx[:500]}")
    history[-1] = (prompt, f"### 🧠 Plan\n{plan}\n\n### 🔍 Research\n{research}\n\n---\n💻 **Coder Agent writing code...**")
    yield history, ""
    
    code = await orchestrator.coder(prompt, research + "\n" + rag_ctx)
    critique = await orchestrator.critic(code)
    
    final_md = f"""### 🧠 Plan
{plan}

### 🔍 Research
{research}

### 💻 Generated Code
{code}

### ✅ Critic Review
{critique}

---
*Model: gpt-4o-mini | RAG docs: {len(rag_results)} | Status: {api_status}*
"""
    history[-1] = (prompt, final_md)
    yield history, ""

def handle_ingest(file):
    if file is None: return "No file"
    try:
        content = open(file.name, 'r', encoding='utf-8', errors='ignore').read()[:15000]
        doc_id = rag_engine.ingest(content, {"source": os.path.basename(file.name)})
        return f"✅ Indexed: {file.name} | Total: {rag_engine.count()}"
    except Exception as e:
        return f"Error: {e}"

def handle_search(query):
    results = rag_engine.search(query, k=5)
    if not results: return "No results. Upload docs first."
    return "\n\n---\n\n".join([f"**{r['meta'].get('source','doc')}**\n{r['text'][:300]}" for r in results])

with gr.Blocks(theme=gr.themes.Soft(primary_hue="violet", neutral_hue="slate"), title="NEXUS AI OS") as demo:
    gr.Markdown(f"""
# 🧠 NEXUS — Autonomous AI OS + OpenAI
**Status:** {api_status} | **Model:** gpt-4o-mini | **Agents:** 4 online
> Complex swarm, simple UI. Professional GitHub-ready.
""")
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=600, label="Agent Workspace", bubble_full_width=False, markdown=True)
            prompt = gr.Textbox(label="What should NEXUS build?", placeholder="e.g. Build a FastAPI todo app with JWT auth and pytest...", lines=3)
            with gr.Row():
                clear = gr.Button("Clear")
                run_btn = gr.Button("🚀 Generate with GPT-4o + Agents", variant="primary")
        with gr.Column(scale=1):
            gr.Markdown("### 📚 Second Brain")
            file_input = gr.File(label="Upload .txt / .py / .md")
            ingest_btn = gr.Button("Index to Memory")
            ingest_status = gr.Textbox(label="Status")
            gr.Markdown("### 🔍 Search Memory")
            search_box = gr.Textbox(placeholder="Search...")
            search_btn = gr.Button("Search")
            search_results = gr.Markdown()
            gr.Markdown(f"### ⚙️ Config\n{api_status}\n\nAdd key in `.env` file")

    run_btn.click(handle_task, [prompt, chatbot], [chatbot, prompt])
    prompt.submit(handle_task, [prompt, chatbot], [chatbot, prompt])
    clear.click(lambda: [], None, chatbot)
    ingest_btn.click(handle_ingest, file_input, ingest_status)
    search_btn.click(handle_search, search_box, search_results)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
