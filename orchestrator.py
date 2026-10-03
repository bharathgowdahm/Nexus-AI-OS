"""
NEXUS with Real OpenAI Integration - Professional Grade
"""
import asyncio, os
from typing import Dict
from openai import AsyncOpenAI
from nexus_core.config import OPENAI_API_KEY

class AgentOrchestrator:
    def __init__(self):
        api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = "gpt-4o-mini"  # Fast, cheap, trending

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            # Fallback mock if no key (so app doesn't crash)
            return f"[MOCK - Add OPENAI_API_KEY to .env to enable real AI]\nSystem: {system_prompt[:100]}...\nTask: {user_prompt[:200]}"
        
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
            return f"Error: {str(e)} - Check your API key and billing"

    async def planner(self, task: str) -> str:
        system = "You are NEXUS Planner Agent. You are expert at breaking complex software tasks into 3-4 clear steps. Be concise, professional, use bullet points."
        return await self._call_llm(system, f"Plan this task: {task}")

    async def researcher(self, task: str) -> str:
        system = "You are NEXUS Researcher Agent. You find best practices, libraries, and patterns. Return 3-5 key insights."
        return await self._call_llm(system, f"Research best practices for: {task}")

    async def coder(self, task: str, research: str) -> str:
        system = """You are NEXUS Coder Agent - senior Python engineer.
Generate PRODUCTION-READY, CLEAN, commented Python code.
- Use FastAPI, Pydantic, type hints
- Include docstrings
- Handle errors
- Return ONLY code in ```python block, no extra explanation."""
        user = f"Task: {task}\n\nResearch context: {research}\n\nGenerate complete working code:"
        return await self._call_llm(system, user)

    async def critic(self, code: str) -> str:
        system = "You are NEXUS Critic Agent. Review code for security, performance, bugs. Score out of 100 and give 2 suggestions."
        return await self._call_llm(system, f"Review this code:\n{code[:3000]}")

    async def execute_full(self, task: str, rag_context: str = "") -> Dict:
        plan = await self.planner(task)
        research = await self.researcher(task + f"\nContext: {rag_context}")
        code = await self.coder(task, research + "\n" + rag_context)
        critique = await self.critic(code)
        return {
            "task": task,
            "plan": plan,
            "research": research,
            "code": code,
            "critique": critique,
            "model": self.model,
            "status": "completed"
        }
