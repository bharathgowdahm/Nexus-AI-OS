import json
import os
import sys

import fastapi
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

app = FastAPI()


@app.exception_handler(Exception)
async def on_error(request: Request, exc: Exception):
    return JSONResponse({"error": f"Server error: {type(exc).__name__}: {exc}"}, status_code=500)

PROMPTS = {
    "chat": "You are NEXUS, a precise, friendly expert assistant. Answer in Markdown. Be concise unless asked for depth.",
    "agent": (
        "You are NEXUS Agent, a team of four experts. For every request answer with these Markdown sections in order: "
        "## Plan (4 clear steps and the tech stack), ## Research (best practices, libraries, pitfalls), "
        "## Code (complete, production-ready code in fenced blocks), ## Review (honest critique, score /100, next steps)."
    ),
    "code": (
        "You are a senior staff engineer. Return complete, production-ready, well-structured code in fenced blocks, "
        "then a short note on how to run it."
    ),
}
MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]


def fail(msg, status=500):
