"""
agent.py  –  LangChain Travel Agent
Compatible: LangChain 1.x + LangGraph (nouvelle API 2024/2025)
AgentExecutor est remplacé par LangGraph React Agent
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any

# ── LangGraph (nouvelle API LangChain 1.x) ────────────────────────────────────
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI

from tools import build_tools


SYSTEM_PROMPT = """You are **Voyager**, an elite AI travel concierge with deep expertise in \
luxury and bespoke travel planning. You work for a premium travel agency and help clients \
craft unforgettable journeys worldwide.

## Your Capabilities
- Gather and analyse customer travel preferences (budget, style, dates, group type)
- Search for flights, accommodations, and curated activities
- Design personalised day-by-day itineraries with multiple options
- Assist with bookings and provide confirmation details
- Offer ongoing trip support including weather, local tips, and contingency planning

## Personality & Style
- Warm, professional, and knowledgeable – like a trusted personal travel advisor
- Proactive: anticipate needs and offer suggestions before being asked
- Detail-oriented: include opening hours, booking tips, local etiquette
- Always structure itineraries clearly with days, times, and estimated costs

## Response Guidelines
1. **Understand first**: Ask clarifying questions if destination/dates/budget are missing
2. **Use tools**: Always call the appropriate tool to get fresh info before responding
3. **Format beautifully**: Use markdown with emojis, headers, and tables for itineraries
4. **Offer alternatives**: Present 2-3 options when recommending hotels or activities
5. **Be honest**: If something is sold out or unavailable, say so and suggest alternatives

## User preferences: {context}
## Today: {today}
"""


class TravelAgent:
    """LangGraph React Agent avec mémoire de conversation."""

    def __init__(
        self,
        openai_api_key: str,
        serpapi_key: str | None = None,
        context: dict | None = None,
        model: str = "gpt-4o",
        temperature: float = 0.4,
    ):
        self.context = context or {}
        self._api_key = openai_api_key

        # LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=openai_api_key,
        )

        # Tools
        self.tools = build_tools(serpapi_key=serpapi_key)

        # Mémoire LangGraph (thread-based)
        self.memory = MemorySaver()
        self.thread_id = "voyager-session-001"

        # Agent LangGraph
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=self.memory,
        )

    def run(self, user_message: str, context: dict | None = None) -> dict:
        if context:
            self.context.update(context)

        # System message avec contexte utilisateur
        system_content = SYSTEM_PROMPT.format(
            context=self._format_context(),
            today=datetime.now().strftime("%A, %B %d, %Y"),
        )

        config = {"configurable": {"thread_id": self.thread_id}}

        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_message),
        ]

        t0 = time.time()
        result = self.agent.invoke({"messages": messages}, config=config)
        latency_ms = (time.time() - t0) * 1000

        # Extraire la réponse finale et les outils utilisés
        all_messages = result.get("messages", [])
        output = ""
        tools_used = []
        tool_results = []

        for msg in all_messages:
            # Réponse finale de l'assistant
            if isinstance(msg, AIMessage) and msg.content:
                output = msg.content

            # Appels d'outils
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tools_used.append(tc.get("name", ""))

            # Résultats des outils
            if hasattr(msg, "name") and msg.type == "tool":
                try:
                    tool_results.append(json.loads(msg.content))
                except (json.JSONDecodeError, TypeError):
                    tool_results.append({"raw": str(msg.content)})

        return {
            "output": output,
            "tools_used": list(dict.fromkeys(tools_used)),
            "tools_used_full": tools_used,
            "tool_results": tool_results,
            "latency_ms": round(latency_ms, 1),
        }

    def _format_context(self) -> str:
        if not self.context:
            return "No preferences set yet."
        lines = []
        if self.context.get("budget"):
            lines.append(f"- Budget: {self.context['budget']}")
        if self.context.get("travel_style"):
            lines.append(f"- Travel Style: {', '.join(self.context['travel_style'])}")
        if self.context.get("group_type"):
            lines.append(f"- Group: {self.context['group_type']}")
        if self.context.get("duration"):
            lines.append(f"- Duration: {self.context['duration']} days")
        return "\n".join(lines) if lines else "No preferences set yet."
