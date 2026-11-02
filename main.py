import json
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

app = FastAPI()

PROMPTS = {
    "chat": "You are NEXUS, a precise, friendly expert assistant. Answer in Markdown.",
    "agent": "You are NEXUS Agent. Answer with these Markdown sections in order: ## Plan, ## Research, ## Code (complete code in fenced blocks), ## Review (critique and score /100).",
    "code": "You are a senior engineer. Return complete, production-ready code in fenced blocks, then a short note on how to run it.",
}
MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]


def fail(msg, status=500):
    return JSONResponse({"error": msg}, status_code=status)


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML


@app.get("/api/health")
async def health():
    return {"ok": True, "key_set": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))}


@app.post("/api/chat")
async def chat(request: Request):
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    if not key:
        return fail("No API key set. Add GEMINI_API_KEY in Vercel > Settings > Environment Variables, then redeploy.")
    if key.startswith("AQ."):
        return fail('That is an OAuth token. Gemini needs an API key that starts with "AIza".')
    try:
        body = await request.json()
        messages = body["messages"]
        assert isinstance(messages, list) and messages
    except Exception:
        return fail("Invalid request.", 400)
    model = body.get("model") if body.get("model") in MODELS else MODELS[0]
    payload = {
        "system_instruction": {"parts": [{"text": PROMPTS.get(body.get("mode"), PROMPTS["chat"])}]},
        "contents": [
            {"role": "model" if m.get("role") == "assistant" else "user", "parts": [{"text": str(m.get("content") or " ")}]}
            for m in messages
        ],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }
    if body.get("web"):
        payload["tools"] = [{"google_search": {}}]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"
    client = httpx.AsyncClient(timeout=120)
    try:
        r = await client.send(client.build_request("POST", url, headers={"x-goog-api-key": key}, json=payload), stream=True)
    except httpx.HTTPError as e:
        await client.aclose()
        return fail(f"Could not reach Gemini ({e.__class__.__name__}).", 502)
    if r.status_code != 200:
        detail = (await r.aread()).decode("utf-8", "ignore")[:300]
        await r.aclose()
        await client.aclose()
        return fail(f"Gemini {r.status_code}: {detail}", r.status_code)

    async def stream():
        try:
            async for line in r.aiter_lines():
                if not line.startswith("data:"):
                    continue
                try:
                    parts = json.loads(line[5:])["candidates"][0]["content"]["parts"]
                except Exception:
                    continue
                text = "".join(p.get("text", "") for p in parts)
                if text:
                    yield text
        except httpx.HTTPError:
            yield "\n\n⚠️ Connection to Gemini was interrupted."
        finally:
            await r.aclose()
            await client.aclose()

    return StreamingResponse(stream(), media_type="text/plain; charset=utf-8", headers={"Cache-Control": "no-store"})


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEXUS</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<style>
:root{--bg:#f6f7fb;--sf:#fff;--s2:#eceef7;--tx:#14172b;--mu:#656a8c;--bd:#dfe2f0;--ac:#4f46e5;--a2:#e9ebff}
@media(prefers-color-scheme:dark){:root{--bg:#0d0f1c;--sf:#151933;--s2:#1c2142;--tx:#e9ebfa;--mu:#9199c4;--bd:#262c52;--ac:#8b93ff;--a2:#20264d}}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--tx);font:15px/1.6 system-ui,sans-serif;height:100dvh}
button,select,textarea{font:inherit;color:inherit}button{cursor:pointer;background:none;border:0}
.app{display:flex;height:100%}
.side{width:260px;background:var(--sf);border-right:1px solid var(--bd);padding:14px;display:flex;flex-direction:column;gap:8px;overflow:auto}
.side b{font-size:20px}
.new,.send{background:var(--ac);color:var(--bg);border-radius:10px;padding:8px 14px;font-weight:600}
.item{display:flex;border-radius:8px;color:var(--mu)}.item:hover,.item.on{background:var(--s2);color:var(--tx)}
.item button:first-child{flex:1;min-width:0;text-align:left;padding:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:inherit}
.main{flex:1;display:flex;flex-direction:column;min-width:0}
.top{display:flex;gap:8px;align-items:center;padding:10px 14px;border-bottom:1px solid var(--bd)}
#seg{display:flex;gap:6px}
.top button,.top select{background:var(--s2);border-radius:8px;padding:5px 12px}
.top .on{background:var(--ac);color:var(--bg)}
.menu{display:none}
.msgs{flex:1;overflow:auto;padding:20px 14px}.col{max-width:740px;margin:0 auto}
h1{font-size:clamp(32px,7vw,54px);line-height:1.05;letter-spacing:-.04em;padding:8vh 0 8px}
.msg{margin-bottom:22px}.u{display:flex;justify-content:flex-end}
.u div{background:var(--a2);border-radius:16px 16px 4px 16px;padding:9px 14px;max-width:85%;white-space:pre-wrap;overflow-wrap:anywhere}
.md>*+*{margin-top:12px}.md ul,.md ol{padding-left:22px}
.md table{border-collapse:collapse;display:block;overflow:auto}.md td,.md th{border:1px solid var(--bd);padding:5px 9px}
.md :not(pre)>code{background:var(--s2);padding:2px 5px;border-radius:5px;font-size:13px}
.cb{border-radius:12px;overflow:hidden;background:#0d1117;color:#e6edf3}
.cbh{display:flex;justify-content:space-between;padding:6px 12px;background:#1b2230;color:#9aa4b8;font-size:12px}
.cb pre{overflow:auto;padding:14px;font:13px/1.5 ui-monospace,monospace}.cb code.hljs{background:none;padding:0}
.err{color:#e5533d}.tools{margin-top:6px;font-size:13px;color:var(--mu)}
.comp{padding:0 14px 14px}
.box{max-width:740px;margin:0 auto;display:flex;gap:8px;align-items:flex-end;background:var(--sf);border:1px solid var(--bd);border-radius:18px;padding:8px 8px 8px 14px}
textarea{flex:1;border:0;background:none;resize:none;outline:0;max-height:180px;padding:6px 0}
@media(max-width:800px){.side{position:fixed;inset:0 auto 0 0;z-index:5;transform:translateX(-100%)}.side.open{transform:none}.menu{display:block}}
</style></head>
<body><div class="app">
<aside class="side" id="side"><b>NEXUS</b><button class="new" data-a="new">New chat</button><nav id="list"></nav></aside>
<main class="main">
<header class="top"><button class="menu" data-a="menu">☰</button>
<span id="seg"><button data-m="chat" class="on">Chat</button><button data-m="agent">Agent</button><button data-m="code">Code</button></span>
<select id="model"><option>gemini-2.5-flash</option><option>gemini-2.5-pro</option><option>gemini-2.0-flash</option></select>
<button id="web" data-a="web">Web</button></header>
<section class="msgs" id="scroll"><div class="col"><h1 id="hero">What are we building today?</h1><div id="msgs"></div></div></section>
<footer class="comp"><div class="box"><textarea id="in" rows="1" placeholder="Ask anything…"></textarea><button class="send" id="send">Send</button></div></footer>
</main></div>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>
const $=s=>document.querySelector(s);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let chats=[];try{chats=JSON.parse(localStorage.getItem('nexus.chats')||'[]')}catch{}
let cid=null,busy=false,mode='chat',web=false,ac=null,raf;
const cur=()=>chats.find(c=>c.id===cid);
const save=()=>{try{localStorage.setItem('nexus.chats',JSON.stringify(chats.slice(0,50)))}catch{}};
marked.use({renderer:{code(code,lang){const l=hljs.getLanguage(lang||'')?lang:'plaintext';
  return `<div class="cb"><div class="cbh"><span>${esc(lang||'text')}</span><button data-copy>Copy</button></div><pre><code class="hljs">${hljs.highlight(code,{language:l}).value}</code></pre></div>`}}});
function render(){
  const c=cur(),m=c?c.messages:[];$('#hero').hidden=m.length>0;
  $('#msgs').innerHTML=m.map((x,i)=>x.role==='user'?`<div class="msg u"><div>${esc(x.content)}</div></div>`
    :`<div class="msg">${x.error?`<p class="err">${esc(x.content)}</p>`:`<div class="md">${DOMPurify.sanitize(marked.parse(x.content||'…'))}</div>`}${i===m.length-1&&!busy&&x.content&&!x.error?'<div class="tools"><button data-a="regen">Regenerate</button></div>':''}</div>`).join('');
  $('#list').innerHTML=chats.map(c=>`<div class="item${c.id===cid?' on':''}"><button data-open="${c.id}">${esc(c.title)}</button><button data-del="${c.id}" aria-label="Delete">✕</button></div>`).join('');
}
function draw(){cancelAnimationFrame(raf);raf=requestAnimationFrame(()=>{const s=$('#scroll'),n=s.scrollHeight-s.scrollTop-s.clientHeight<150;render();if(n)s.scrollTop=s.scrollHeight})}
async function run(c,hist){
  ac=new AbortController();busy=true;$('#send').textContent='Stop';
  c.messages=[...hist,{role:'assistant',content:''}];draw();
  try{
    const r=await fetch('/api/chat',{method:'POST',signal:ac.signal,headers:{'Content-Type':'application/json'},
      body:JSON.stringify({messages:hist.map(({role,content})=>({role,content})),mode,web,model:$('#model').value})});
    if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||'Request failed ('+r.status+')');
    const rd=r.body.getReader(),dec=new TextDecoder();let acc='';
    for(;;){const{done,value}=await rd.read();if(done)break;acc+=dec.decode(value,{stream:true});c.messages.at(-1).content=acc;draw()}
  }catch(e){if(e.name!=='AbortError')Object.assign(c.messages.at(-1),{content:e.message,error:true})}
  if(!c.messages.at(-1).content)c.messages.pop();
  busy=false;$('#send').textContent='Send';render();save();
}
function send(t){
  t=(t??$('#in').value).trim();if(!t||busy)return;
  let c=cur();if(!c){c={id:Math.random().toString(36).slice(2,9),title:t.slice(0,40),messages:[]};chats.unshift(c);cid=c.id}
  $('#in').value='';$('#in').style.height='auto';run(c,[...c.messages,{role:'user',content:t}]);
}
document.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;const d=b.dataset;
  if(d.m){mode=d.m;document.querySelectorAll('#seg button').forEach(x=>x.classList.toggle('on',x===b))}
  else if(d.open){cid=d.open;$('#side').classList.remove('open');render()}
  else if(d.del){chats=chats.filter(c=>c.id!==d.del);if(cid===d.del)cid=null;save();render()}
  else if(d.a==='new'){cid=null;$('#side').classList.remove('open');render()}
  else if(d.a==='menu')$('#side').classList.toggle('open');
  else if(d.a==='web'){web=!web;b.classList.toggle('on',web)}
  else if(d.a==='regen'&&!busy){const c=cur();run(c,c.messages.slice(0,-1))}
  else if('copy' in d){navigator.clipboard.writeText(b.closest('.cb').querySelector('code').innerText);b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1500)}
});
$('#send').onclick=()=>busy?ac.abort():send();
$('#in').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
$('#in').addEventListener('input',e=>{e.target.style.height='auto';e.target.style.height=e.target.scrollHeight+'px'});
render();
</script></body></html>
"""

# --- end of main.py ---
