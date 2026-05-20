"""
metrics.py  –  Couche d'évaluation Voyager AI
==============================================
Implémente les 4 niveaux de métriques définis dans la Guideline Technique :
  1. Métriques de Retrieval (RAG)
  2. Métriques de Génération
  3. Métriques du Pipeline Agentique
  4. Évaluation qualitative via LLM Juge

Architecture : séparation stricte entre logique métier et logique d'évaluation.
"""

from __future__ import annotations

import json
import time
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


# ══════════════════════════════════════════════════════════════════════════════
# 1. MÉTRIQUES DE RETRIEVAL
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RetrievalMetrics:
    """Section 4 du guideline – Évaluation de la qualité du retrieval."""

    # Volume
    raw_count: int = 0           # Nombre de documents récupérés
    selected_count: int = 0      # Documents retenus après filtrage

    # Scores de similarité
    top_1_raw_score: float = 0.0  # Score du meilleur document
    avg_raw_score: float = 0.0    # Score moyen

    # Compression
    compression_ratio: float = 0.0  # selected / raw

    # Diagnostics
    empty_retrieval: bool = False   # Aucun document retourné
    over_retrieval: bool = False    # Trop de documents (> seuil)
    under_retrieval: bool = False   # Trop peu de documents (< seuil)

    # Horodatage
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def compute(
        cls,
        tool_results: list[dict],
        raw_threshold_high: int = 10,
        raw_threshold_low: int = 1,
    ) -> "RetrievalMetrics":
        """
        Calcule les métriques à partir des résultats des outils de recherche.

        tool_results : liste de dict issus des tools search_flights / search_hotels
        """
        m = cls()

        # Compter les documents issus des tools de recherche
        all_items = []
        for r in tool_results:
            if "flights" in r:
                all_items.extend(r["flights"])
            if "hotels" in r:
                all_items.extend(r["hotels"])
            if "activities" in r:
                all_items.extend(r.get("activities", []))

        m.raw_count = len(all_items)

        # Simuler un filtrage (ex: score > seuil)
        scores = [item.get("rating", item.get("price_usd", 0)) for item in all_items]
        if scores:
            m.top_1_raw_score = round(max(scores), 3)
            m.avg_raw_score = round(sum(scores) / len(scores), 3)

        # Sélection : on conserve les items avec rating >= 4.0 ou prix raisonnable
        selected = [
            item for item in all_items
            if item.get("rating", 5) >= 4.0 or item.get("stars", 3) >= 3
        ]
        m.selected_count = len(selected)

        # Compression ratio
        if m.raw_count > 0:
            m.compression_ratio = round(m.selected_count / m.raw_count, 3)

        # Diagnostics
        m.empty_retrieval = m.raw_count == 0
        m.over_retrieval = m.raw_count > raw_threshold_high
        m.under_retrieval = m.raw_count < raw_threshold_low

        return m


# ══════════════════════════════════════════════════════════════════════════════
# 2. MÉTRIQUES DE GÉNÉRATION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class GenerationMetrics:
    """Section 5 du guideline – Évaluation de la réponse générée."""

    # Présence
    has_answer: bool = False        # Réponse non vide

    # Grounding
    grounded: bool = False          # Réponse basée sur des documents
    potential_hallucination: bool = False

    # Longueurs
    answer_length: int = 0          # Taille de la réponse (chars)
    context_length: int = 0         # Taille du contexte fourni

    # Ratio de compression
    compression_ratio: float = 0.0  # answer / context

    # Diagnostics
    answer_too_short: bool = False   # < 50 chars
    answer_too_long: bool = False    # > 3000 chars

    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def compute(
        cls,
        answer: str,
        context: str,
        tools_used: list[str],
        min_length: int = 50,
        max_length: int = 3000,
    ) -> "GenerationMetrics":
        m = cls()

        m.has_answer = bool(answer and answer.strip())
        m.answer_length = len(answer) if answer else 0
        m.context_length = len(context) if context else 0

        # Grounding : la réponse utilise-t-elle des outils de recherche ?
        search_tools = {"search_flights", "search_hotels", "search_activities",
                        "build_itinerary", "get_weather_forecast", "get_travel_advisory"}
        m.grounded = bool(set(tools_used) & search_tools)
        m.potential_hallucination = m.has_answer and not m.grounded

        # Ratio de compression
        if m.context_length > 0:
            m.compression_ratio = round(m.answer_length / m.context_length, 3)

        # Diagnostics
        m.answer_too_short = m.answer_length < min_length
        m.answer_too_long = m.answer_length > max_length

        return m


# ══════════════════════════════════════════════════════════════════════════════
# 3. MÉTRIQUES DU PIPELINE AGENTIQUE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgenticMetrics:
    """Section 6 du guideline – Évaluation du pipeline multi-agents."""

    # Présence des étapes clés
    has_summary: bool = False       # Synthèse produite
    has_analysis: bool = False      # Raisonnement produit
    has_answer: bool = False        # Sortie finale
    has_review: bool = False        # Supervision / revue

    # Complexité
    execution_steps: int = 0        # Nombre d'étapes totales
    agents_used: int = 0            # Nombre d'outils/agents distincts

    # Complétude
    pipeline_complete: bool = False # Étapes essentielles présentes
    has_supervision: bool = False   # Contrôle qualité actif

    # Performance
    steps_per_agent: float = 0.0    # Charge moyenne par agent
    latency_ms: float = 0.0        # Temps d'exécution total

    # Détail des outils utilisés
    tools_sequence: list = field(default_factory=list)

    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def compute(
        cls,
        tools_used: list[str],
        answer: str,
        latency_ms: float = 0.0,
    ) -> "AgenticMetrics":
        m = cls()
        m.tools_sequence = tools_used
        m.latency_ms = round(latency_ms, 1)

        # Présence des étapes
        search_tools = {"search_flights", "search_hotels", "search_activities"}
        analysis_tools = {"build_itinerary", "get_travel_advisory", "convert_currency"}
        supervision_tools = {"get_weather_forecast"}  # En vrai : outil de revue

        m.has_summary = bool(set(tools_used) & search_tools)
        m.has_analysis = bool(set(tools_used) & analysis_tools)
        m.has_answer = bool(answer and answer.strip())
        m.has_review = bool(set(tools_used) & supervision_tools)

        # Complexité
        m.execution_steps = len(tools_used)
        m.agents_used = len(set(tools_used))

        # Complétude : recherche + analyse + réponse
        m.pipeline_complete = m.has_summary and m.has_analysis and m.has_answer
        m.has_supervision = m.has_review

        # Charge par agent
        if m.agents_used > 0:
            m.steps_per_agent = round(m.execution_steps / m.agents_used, 2)

        return m


# ══════════════════════════════════════════════════════════════════════════════
# 4. LLM JUGE – Évaluation qualitative
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class LLMJudgeMetrics:
    """Section 7 du guideline – Évaluation sémantique via LLM juge."""

    pertinence: int = 0         # 1-5 : la réponse répond-elle à la question ?
    fidelite: int = 0           # 1-5 : fidélité au contexte / documents
    completude: int = 0         # 1-5 : tous les aspects sont-ils couverts ?
    clarte: int = 0             # 1-5 : la réponse est-elle claire et structurée ?
    score_global: float = 0.0   # Moyenne pondérée

    verdict: str = ""           # EXCELLENT / BON / ACCEPTABLE / INSUFFISANT
    justification: str = ""     # Explication du LLM juge
    recommandations: list = field(default_factory=list)

    judge_model: str = "gpt-4o-mini"
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def compute(
        cls,
        question: str,
        answer: str,
        context: str,
        openai_api_key: str,
        model: str = "gpt-4o-mini",
    ) -> "LLMJudgeMetrics":
        m = cls()
        m.judge_model = model

        judge_prompt = f"""Tu es un évaluateur expert en systèmes d'IA pour le secteur du voyage.
Évalue la réponse suivante selon 4 critères, chacun noté de 1 (mauvais) à 5 (excellent).

QUESTION POSÉE :
{question}

CONTEXTE / OUTILS UTILISÉS :
{context[:800] if context else "Aucun contexte fourni"}

RÉPONSE GÉNÉRÉE :
{answer[:1500] if answer else "Aucune réponse"}

---
Réponds UNIQUEMENT en JSON avec ce format exact :
{{
  "pertinence": <1-5>,
  "fidelite": <1-5>,
  "completude": <1-5>,
  "clarte": <1-5>,
  "justification": "<2-3 phrases d'explication>",
  "recommandations": ["<conseil 1>", "<conseil 2>"]
}}
"""

        try:
            llm = ChatOpenAI(model=model, temperature=0, api_key=openai_api_key)
            response = llm.invoke([
                SystemMessage(content="Tu es un évaluateur IA expert. Réponds uniquement en JSON valide."),
                HumanMessage(content=judge_prompt),
            ])
            raw = response.content.strip()
            # Nettoyer les balises markdown si présentes
            raw = re.sub(r"```json|```", "", raw).strip()
            data = json.loads(raw)

            m.pertinence = int(data.get("pertinence", 0))
            m.fidelite = int(data.get("fidelite", 0))
            m.completude = int(data.get("completude", 0))
            m.clarte = int(data.get("clarte", 0))
            m.justification = data.get("justification", "")
            m.recommandations = data.get("recommandations", [])

            # Score global pondéré (pertinence et fidélité plus importants)
            m.score_global = round(
                (m.pertinence * 0.35 + m.fidelite * 0.30 +
                 m.completude * 0.20 + m.clarte * 0.15), 2
            )

            # Verdict
            if m.score_global >= 4.5:
                m.verdict = "EXCELLENT"
            elif m.score_global >= 3.5:
                m.verdict = "BON"
            elif m.score_global >= 2.5:
                m.verdict = "ACCEPTABLE"
            else:
                m.verdict = "INSUFFISANT"

        except Exception as e:
            m.justification = f"Évaluation LLM juge indisponible : {str(e)}"
            m.verdict = "NON_ÉVALUÉ"

        return m


# ══════════════════════════════════════════════════════════════════════════════
# 5. RAPPORT CONSOLIDÉ
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EvaluationReport:
    """Rapport d'évaluation complet – agrège les 4 couches de métriques."""

    turn_id: str = ""
    question: str = ""
    retrieval: Optional[RetrievalMetrics] = None
    generation: Optional[GenerationMetrics] = None
    agentic: Optional[AgenticMetrics] = None
    judge: Optional[LLMJudgeMetrics] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "question": self.question,
            "created_at": self.created_at,
            "retrieval": self.retrieval.to_dict() if self.retrieval else None,
            "generation": self.generation.to_dict() if self.generation else None,
            "agentic": self.agentic.to_dict() if self.agentic else None,
            "judge": self.judge.to_dict() if self.judge else None,
        }

    def summary(self) -> dict:
        """Vue synthétique pour l'affichage dashboard."""
        return {
            "retrieval_docs": self.retrieval.raw_count if self.retrieval else 0,
            "retrieval_selected": self.retrieval.selected_count if self.retrieval else 0,
            "grounded": self.generation.grounded if self.generation else False,
            "hallucination_risk": self.generation.potential_hallucination if self.generation else False,
            "pipeline_complete": self.agentic.pipeline_complete if self.agentic else False,
            "tools_used": self.agentic.agents_used if self.agentic else 0,
            "latency_ms": self.agentic.latency_ms if self.agentic else 0,
            "judge_score": self.judge.score_global if self.judge else None,
            "judge_verdict": self.judge.verdict if self.judge else "N/A",
        }


# ══════════════════════════════════════════════════════════════════════════════
# 6. ÉVALUATEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class TravelEvaluator:
    """
    Orchestre l'évaluation complète d'un tour de conversation.
    À appeler APRÈS chaque réponse de l'agent – totalement découplé du code métier.
    """

    def __init__(self, openai_api_key: str, enable_llm_judge: bool = True):
        self.openai_api_key = openai_api_key
        self.enable_llm_judge = enable_llm_judge
        self.history: list[EvaluationReport] = []

    def evaluate(
        self,
        question: str,
        answer: str,
        tools_used: list[str],
        tool_results: list[dict] | None = None,
        latency_ms: float = 0.0,
        turn_id: str | None = None,
    ) -> EvaluationReport:
        """
        Évalue un tour complet et retourne un rapport consolidé.

        Paramètres
        ----------
        question    : question posée par l'utilisateur
        answer      : réponse produite par l'agent
        tools_used  : liste des noms d'outils appelés
        tool_results: résultats bruts des outils (pour les métriques retrieval)
        latency_ms  : temps de réponse total en millisecondes
        turn_id     : identifiant unique du tour (auto-généré si absent)
        """
        import uuid
        report = EvaluationReport(
            turn_id=turn_id or str(uuid.uuid4())[:8],
            question=question,
        )

        # 1. Retrieval
        report.retrieval = RetrievalMetrics.compute(tool_results or [])

        # 2. Génération
        context_summary = f"Tools: {', '.join(tools_used)}" if tools_used else ""
        report.generation = GenerationMetrics.compute(
            answer=answer,
            context=context_summary,
            tools_used=tools_used,
        )

        # 3. Agentique
        report.agentic = AgenticMetrics.compute(
            tools_used=tools_used,
            answer=answer,
            latency_ms=latency_ms,
        )

        # 4. LLM Juge (optionnel)
        if self.enable_llm_judge and self.openai_api_key:
            report.judge = LLMJudgeMetrics.compute(
                question=question,
                answer=answer,
                context=context_summary,
                openai_api_key=self.openai_api_key,
            )

        self.history.append(report)
        return report

    def get_aggregated_stats(self) -> dict:
        """Statistiques agrégées sur toutes les évaluations de la session."""
        if not self.history:
            return {}

        n = len(self.history)
        grounded_count = sum(1 for r in self.history if r.generation and r.generation.grounded)
        complete_count = sum(1 for r in self.history if r.agentic and r.agentic.pipeline_complete)
        hallucination_count = sum(1 for r in self.history if r.generation and r.generation.potential_hallucination)
        judge_scores = [r.judge.score_global for r in self.history if r.judge and r.judge.score_global > 0]

        return {
            "total_turns": n,
            "grounded_rate": round(grounded_count / n * 100, 1),
            "pipeline_complete_rate": round(complete_count / n * 100, 1),
            "hallucination_risk_rate": round(hallucination_count / n * 100, 1),
            "avg_judge_score": round(sum(judge_scores) / len(judge_scores), 2) if judge_scores else None,
            "avg_latency_ms": round(
                sum(r.agentic.latency_ms for r in self.history if r.agentic) / n, 1
            ),
            "avg_tools_per_turn": round(
                sum(r.agentic.agents_used for r in self.history if r.agentic) / n, 1
            ),
        }
