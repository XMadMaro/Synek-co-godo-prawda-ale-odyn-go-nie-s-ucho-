"""
Judge-Dredd Agent - Verdict Generator
Full implementation with RAG retrieval and LLM-based evaluation.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from src.agents.base import BaseAgent
from src.core import get_settings, get_logger
from src.core.models import (
    Discrepancy,
    Evidence,
    QuestionAnswer,
    Verdict,
    VerdictCategory,
)
from src.infrastructure import LLMClient, QdrantService


@dataclass
class JudgeInput:
    """Input for Judge-Dredd agent."""
    qa_pairs: list[QuestionAnswer]
    rag_collection: str = "knowledge_base"
    top_k: int = 5
    use_anthropic: bool = False  # Use Claude for stricter evaluation


class JudgeDreddAgent(BaseAgent[JudgeInput, list[Verdict]]):
    """
    Verdict generator agent.

    Responsibilities:
    1. For each Q&A pair, retrieve relevant context from RAG
    2. Compare chatbot answer with authoritative sources
    3. Categorize discrepancies (error, hallucination, partial)
    4. Generate verdict with confidence score and explanation
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        qdrant_service: QdrantService | None = None,
    ):
        super().__init__("judge_dredd")
        self.settings = get_settings()
        self.llm = llm_client or LLMClient()
        self.qdrant = qdrant_service or QdrantService()

    async def execute(self, input_data: JudgeInput) -> list[Verdict]:
        """
        Evaluate all Q&A pairs and generate verdicts.
        """
        self.log.info(
            "judgment_started",
            questions_count=len(input_data.qa_pairs),
            collection=input_data.rag_collection,
        )

        verdicts: list[Verdict] = []

        for idx, qa in enumerate(input_data.qa_pairs):
            try:
                self.log.debug(
                    "evaluating_question",
                    index=idx + 1,
                    question=qa.question[:100],
                )

                verdict = await self._evaluate_single(
                    qa,
                    input_data.rag_collection,
                    input_data.top_k,
                )
                verdicts.append(verdict)

            except Exception as e:
                self.log.error(
                    "evaluation_failed",
                    question_id=qa.question_id,
                    error=str(e),
                )
                # Create fallback verdict
                verdicts.append(
                    Verdict(
                        question_id=qa.question_id,
                        question=qa.question,
                        chatbot_answer=qa.answer,
                        category=VerdictCategory.NO_DATA,
                        confidence=0.0,
                        explanation=f"Evaluation failed: {e}",
                    )
                )

        # Log summary
        summary = self._summarize_verdicts(verdicts)
        self.log.info("judgment_completed", summary=summary)

        return verdicts

    async def _evaluate_single(
        self,
        qa: QuestionAnswer,
        collection: str,
        top_k: int,
    ) -> Verdict:
        """
        Evaluate a single Q&A pair.

        Steps:
        1. Retrieve relevant context from RAG
        2. Build evaluation prompt
        3. Call LLM for verdict
        4. Parse and return structured verdict
        """
        # Step 1: Retrieve context
        query_embedding = await self.llm.embed([qa.question])
        evidence_list = await self.qdrant.search(
            query_vector=query_embedding[0],
            collection=collection,
            top_k=top_k,
            min_score=self.settings.rag_min_similarity,
        )

        # Step 2: Build and send evaluation prompt
        messages = self._build_evaluation_messages(qa, evidence_list)

        # Step 3: Call LLM for JSON response
        try:
            response = await self.llm.chat_json(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent evaluation
            )
        except Exception as e:
            self.log.warning("json_parse_failed", error=str(e))
            # Fallback to text response
            text_response = await self.llm.chat(messages=messages, temperature=0.1)
            response = self._parse_text_response(text_response)

        # Step 4: Parse response into Verdict
        return self._build_verdict(qa, evidence_list, response)

    def _build_evaluation_messages(
        self,
        qa: QuestionAnswer,
        evidence: list[Evidence],
    ) -> list[dict[str, str]]:
        """Build the evaluation prompt for LLM."""

        # Format evidence
        if evidence:
            evidence_text = "\n\n".join(
                f"[Źródło {i+1}: {e.source_url}]\n{e.content}"
                for i, e in enumerate(evidence)
            )
        else:
            evidence_text = "BRAK KONTEKSTU - nie znaleziono odpowiednich źródeł."

        system_prompt = """Jesteś bezwzględnym sędzią odpowiedzi chatbotów - Judge-Dredd.
Twoje orzeczenia są ostateczne i oparte WYŁĄCZNIE na dostarczonym kontekście.

ZASADY OCENY:
1. POPRAWNA - odpowiedź zgadza się w 100% z kontekstem
2. CZĘŚCIOWO_POPRAWNA - odpowiedź zawiera poprawne I niepoprawne elementy
3. BŁĄD - odpowiedź jest sprzeczna z kontekstem
4. HALUCYNACJA - odpowiedź zawiera informacje NIEOBECNE w kontekście (wymyślone)
5. BRAK_DANYCH - kontekst nie pozwala na ocenę (brak informacji)

WAŻNE:
- Jeśli nie ma kontekstu potwierdzającego ani zaprzeczającego - orzekaj BRAK_DANYCH
- Każda rozbieżność z faktami to BŁĄD
- Informacje wymyślone (nie w kontekście) to HALUCYNACJA
- Confidence powinno odzwierciedlać pewność oceny (0.0-1.0)

Odpowiedz TYLKO w formacie JSON."""

        user_prompt = f"""Oceń poniższą odpowiedź chatbota.

PYTANIE UŻYTKOWNIKA:
{qa.question}

ODPOWIEDŹ CHATBOTA:
{qa.answer}

KONTEKST (źródła prawdy):
{evidence_text}

Wygeneruj werdykt w formacie JSON:
{{
    "category": "POPRAWNA" | "CZĘŚCIOWO_POPRAWNA" | "BŁĄD" | "HALUCYNACJA" | "BRAK_DANYCH",
    "confidence": 0.0-1.0,
    "discrepancies": [
        {{"chatbot_claim": "co powiedział chatbot", "truth": "co mówi kontekst", "severity": "minor|major|critical"}}
    ],
    "explanation": "krótkie uzasadnienie werdyktu"
}}"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_verdict(
        self,
        qa: QuestionAnswer,
        evidence: list[Evidence],
        response: dict[str, Any],
    ) -> Verdict:
        """Build Verdict object from LLM response."""

        # Parse category
        category_str = response.get("category", "BRAK_DANYCH")
        try:
            category = VerdictCategory(category_str)
        except ValueError:
            category = VerdictCategory.NO_DATA

        # Parse discrepancies
        discrepancies = []
        for d in response.get("discrepancies", []):
            discrepancies.append(
                Discrepancy(
                    chatbot_claim=d.get("chatbot_claim", ""),
                    truth=d.get("truth", ""),
                    explanation="",
                    severity=d.get("severity", "minor"),
                )
            )

        return Verdict(
            question_id=qa.question_id,
            question=qa.question,
            chatbot_answer=qa.answer,
            category=category,
            confidence=float(response.get("confidence", 0.5)),
            discrepancies=discrepancies,
            evidence=evidence,
            explanation=response.get("explanation", ""),
        )

    def _parse_text_response(self, text: str) -> dict:
        """Fallback parser for non-JSON responses."""
        # Try to find JSON in response
        import re

        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Default fallback
        return {
            "category": "BRAK_DANYCH",
            "confidence": 0.3,
            "discrepancies": [],
            "explanation": f"Could not parse response: {text[:200]}",
        }

    def _summarize_verdicts(self, verdicts: list[Verdict]) -> dict[str, Any]:
        """Generate summary statistics."""
        summary: dict[str, int] = {}
        total_confidence = 0.0

        for v in verdicts:
            key = v.category.value
            summary[key] = summary.get(key, 0) + 1
            total_confidence += v.confidence

        avg_confidence = total_confidence / len(verdicts) if verdicts else 0

        return {
            "distribution": summary,
            "total": len(verdicts),
            "avg_confidence": round(avg_confidence, 3),
            "accuracy": round(
                summary.get("POPRAWNA", 0) / len(verdicts) * 100 if verdicts else 0,
                1,
            ),
        }

    def _build_system_prompt(self) -> str:
        return """
Jesteś bezwzględnym sędzią odpowiedzi chatbotów - Judge-Dredd.
Twoje orzeczenia są ostateczne i oparte wyłącznie na faktach.
ZASADY:
1. Jeśli nie ma kontekstu potwierdzającego - orzekaj BRAK_DANYCH.
2. Każda rozbieżność z faktami to BŁĄD lub HALUCYNACJA.
3. Częściowo poprawne to nadal niepełne - traktuj surowo.
4. Confidence musi odzwierciedlać pewność, nie być zawyżone.
"""
