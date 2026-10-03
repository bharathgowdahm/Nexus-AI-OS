"""
NEXUS with Real OpenAI + Streamlit Secrets Support - FIXED
"""
import asyncio, os
from typing import Dict
from openai import AsyncOpenAI

def get_key(override=""):
    if override:
        return override
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except:
        pass
    # Try dotenv
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    return os.getenv("OPENAI_API_KEY", "")

class AgentOrchestrator:
    def __init__(self, api_key_override=""):
        api_key = get_key(api_key_override)
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = "gpt-4o-mini"

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            return f"[MOCK MODE - Add key in Streamlit Secrets]\nSystem: {system_prompt[:80]}\nTask: {user_prompt[:300]}..."
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    async def planner(self, task: str) -> str:
        return await self._call_llm("You are NEXUS Planner Agent. Break tasks into 3-4 clear steps.", f"Plan: {task}")

    async def researcher(self, task: str) -> str:
        return await self._call_llm("You are Researcher Agent. Find best practices.", f"Research: {task}")

    async def coder(self, task: str, research: str) -> str:
        system = "You are senior Python engineer. Generate PRODUCTION-READY Python code with FastAPI, type hints, docstrings. Return ONLY code in python block."
        return await self._call_llm(system, f"Task: {task}\nResearch: {research}\nGenerate code:")

    async def critic(self, code: str) -> str:
        return await self._call_llm("You are Critic Agent. Review for security & quality. Score /100.", f"Review:\n{code[:3000]}")

    async def execute_full(self, task: str, rag_context: str = "") -> Dict:
        plan = await self.planner(task)
        research = await self.researcher(task)
        code = await self.coder(task, research + "\n" + rag_context)
        critique = await self.critic(code)
        return {"task": task, "plan": plan, "research": research, "code": code, "critique": critique, "status": "completed"}
