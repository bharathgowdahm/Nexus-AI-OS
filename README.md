
NEXUS — AI workspace (Vercel + FastAPI + Gemini)
Three files, no folders: index.py, requirements.txt, README.md.
Features: streaming Gemini chat · Chat / Agent (plan → research → code → review) / Code modes · Stop & Regenerate ·
saved chat history · Markdown with syntax-highlighted code and Copy · attach text/code files · model picker · light/dark theme.
Deploy
GitHub → New repository → Add file → Upload files → drop all 3 files → Commit.
vercel.com → Add New → Project → import the repo → Deploy.
Settings → Environment Variables: add GEMINI_API_KEY (from https://aistudio.google.com/app/apikey, starts with AIza).
Deployments → Redeploy so the key is picked up.
