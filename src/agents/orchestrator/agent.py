"""
Orchestrator Agent - Main Coordinator
Full implementation connecting all agents into a complete audit pipeline.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.agents.base import BaseAgent
from src.agents.scraper_intel import ScraperIntelAgent, ScrapeRequest
from src.agents.knowledge_architect import KnowledgeArchitectAgent, IndexRequest
from src.agents.chat_interrogator import ChatInterrogatorAgent, InterrogateRequest
from src.agents.judge_dredd import JudgeDreddAgent, JudgeInput
from src.agents.prompt_refiner import PromptRefinerAgent, RefineRequest
from src.core import get_settings, get_logger
from src.core.models import AuditReport, TestQuestion, VerdictCategory
from src.infrastructure import LLMClient, QdrantService


@dataclass
class AuditRequest:
    """Input for Orchestrator agent."""
    target_url: str
    scrape_depth: int = 2
    max_pages: int = 50
    questions_count: int = 20
    generate_prompt_improvement: bool = True
    collection_name: str | None = None  # Auto-generate if not provided
    options: dict[str, Any] = field(default_factory=dict)


class OrchestratorAgent(BaseAgent[AuditRequest, AuditReport]):
    """
    Main coordinator agent for TruthSeeker system.

    Pipeline:
    1. Scraper-Intel → Gather content from website
    2. Knowledge-Architect → Index into RAG
    3. Generate test questions
    4. Chat-Interrogator → Test chatbot
    5. Judge-Dredd → Evaluate responses
    6. (Optional) Prompt-Refiner → Suggest improvements
    7. Compile and return report
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        qdrant_service: QdrantService | None = None,
    ):
        super().__init__("orchestrator")
        self.settings = get_settings()
        self.llm = llm_client or LLMClient()
        self.qdrant = qdrant_service or QdrantService()

        # Initialize sub-agents with shared clients
        self.scraper = ScraperIntelAgent()
        self.knowledge_architect = KnowledgeArchitectAgent(self.llm, self.qdrant)
        self.chat_interrogator = ChatInterrogatorAgent()
        self.judge = JudgeDreddAgent(self.llm, self.qdrant)
        self.prompt_refiner = PromptRefinerAgent(self.llm)

    async def execute(self, input_data: AuditRequest) -> AuditReport:
        """
        Execute the full audit pipeline.
        """
        report_id = f"audit_{uuid.uuid4().hex[:8]}"
        collection = input_data.collection_name or f"kb_{uuid.uuid4().hex[:8]}"

        self.log.info(
            "audit_started",
            report_id=report_id,
            target_url=input_data.target_url,
            collection=collection,
        )

        started_at = datetime.utcnow()

        # =====================================================================
        # Phase 1: Intelligence Gathering (Scraper-Intel)
        # =====================================================================
        self.log.info("phase_started", phase="intelligence_gathering")

        scraped_content = await self.scraper.run(
            ScrapeRequest(
                url=input_data.target_url,
                depth=input_data.scrape_depth,
                max_pages=input_data.max_pages,
            )
        )

        if not scraped_content:
            self.log.error("scraping_failed", url=input_data.target_url)
            return self._create_failed_report(
                report_id, input_data.target_url, "Scraping failed - no content"
            )

        self.log.info(
            "phase_completed",
            phase="intelligence_gathering",
            pages_scraped=len(scraped_content),
        )

        # =====================================================================
        # Phase 2: Knowledge Indexing (Knowledge-Architect)
        # =====================================================================
        self.log.info("phase_started", phase="knowledge_indexing")

        indexed_docs = await self.knowledge_architect.run(
            IndexRequest(
                documents=scraped_content,
                collection_name=collection,
                chunk_size=self.settings.rag_chunk_size,
                chunk_overlap=self.settings.rag_chunk_overlap,
            )
        )

        total_chunks = sum(d.chunks_count for d in indexed_docs)
        self.log.info(
            "phase_completed",
            phase="knowledge_indexing",
            documents=len(indexed_docs),
            chunks=total_chunks,
        )

        # =====================================================================
        # Phase 3: Question Generation
        # =====================================================================
        self.log.info("phase_started", phase="question_generation")

        questions = await self._generate_questions(
            scraped_content,
            input_data.questions_count,
        )

        self.log.info(
            "phase_completed",
            phase="question_generation",
            questions_count=len(questions),
        )

        # =====================================================================
        # Phase 4: Interrogation (Chat-Interrogator)
        # =====================================================================
        self.log.info("phase_started", phase="interrogation")

        session = await self.chat_interrogator.run(
            InterrogateRequest(
                target_url=input_data.target_url,
                questions=questions,
            )
        )

        qa_pairs = self.chat_interrogator.extract_qa_pairs(session)
        self.log.info(
            "phase_completed",
            phase="interrogation",
            qa_pairs=len(qa_pairs),
        )

        # =====================================================================
        # Phase 5: Judgment (Judge-Dredd)
        # =====================================================================
        self.log.info("phase_started", phase="judgment")

        verdicts = await self.judge.run(
            JudgeInput(
                qa_pairs=qa_pairs,
                rag_collection=collection,
            )
        )

        self.log.info(
            "phase_completed",
            phase="judgment",
            verdicts_count=len(verdicts),
        )

        # =====================================================================
        # Phase 6: Prompt Improvement (Optional)
        # =====================================================================
        improved_prompt = None
        if input_data.generate_prompt_improvement:
            self.log.info("phase_started", phase="prompt_improvement")

            errors = [
                v for v in verdicts
                if v.category in [VerdictCategory.ERROR, VerdictCategory.HALLUCINATION]
            ]

            if errors:
                improved = await self.prompt_refiner.run(
                    RefineRequest(verdicts=errors)
                )
                improved_prompt = improved.improved_prompt

            self.log.info("phase_completed", phase="prompt_improvement")

        # =====================================================================
        # Phase 7: Report Generation
        # =====================================================================
        summary = self._calculate_summary(verdicts)
        overall_score = self._calculate_score(verdicts)

        report = AuditReport(
            report_id=report_id,
            target_url=input_data.target_url,
            total_questions=len(verdicts),
            verdicts=verdicts,
            summary=summary,
            overall_score=overall_score,
            created_at=datetime.utcnow(),
        )

        # Add metadata
        duration = (datetime.utcnow() - started_at).total_seconds()
        self.log.info(
            "audit_completed",
            report_id=report_id,
            duration_seconds=duration,
            overall_score=overall_score,
            summary=summary,
        )

        return report

    async def _generate_questions(
        self,
        content: list,
        count: int,
    ) -> list[TestQuestion]:
        """
        Generate test questions based on scraped content.
        Uses LLM to create diverse, relevant questions.
        """
        # Combine content for context
        combined_text = "\n\n".join(
            f"[{c.title}]\n{c.content[:2000]}" for c in content[:5]
        )

        prompt = f"""Na podstawie poniższej treści strony wygeneruj {count} pytań testowych.

Pytania powinny:
1. Być różnorodne (fakty, godziny, procedury, kontakt)
2. Dotyczyć konkretnych informacji ze strony
3. Być naturalne (jak zadałby użytkownik)
4. Zawierać pytania trudne (edge cases)

TREŚĆ STRONY:
{combined_text}

Wygeneruj pytania w formacie JSON:
{{
    "questions": [
        {{"question": "...", "category": "fakty|godziny|procedury|kontakt|inne", "priority": 1-5}}
    ]
}}"""

        try:
            response = await self.llm.chat_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            questions = []
            for i, q in enumerate(response.get("questions", [])[:count]):
                questions.append(
                    TestQuestion(
                        id=f"q_{i+1}",
                        question=q.get("question", ""),
                        category=q.get("category", "inne"),
                        expected_context="",
                        priority=q.get("priority", 3),
                    )
                )

            return questions

        except Exception as e:
            self.log.error("question_generation_failed", error=str(e))
            # Fallback questions
            return [
                TestQuestion(id="q_1", question="Jakie są godziny otwarcia?", category="godziny", expected_context="", priority=1),
                TestQuestion(id="q_2", question="Jak się z wami skontaktować?", category="kontakt", expected_context="", priority=1),
                TestQuestion(id="q_3", question="Jakie usługi oferujecie?", category="usługi", expected_context="", priority=2),
            ]

    def _calculate_summary(self, verdicts: list) -> dict[str, int]:
        """Calculate verdict distribution."""
        summary: dict[str, int] = {}
        for v in verdicts:
            key = v.category.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    def _calculate_score(self, verdicts: list) -> float:
        """Calculate overall accuracy score (0-100)."""
        if not verdicts:
            return 0.0

        correct = sum(
            1 for v in verdicts
            if v.category == VerdictCategory.CORRECT
        )
        partial = sum(
            1 for v in verdicts
            if v.category == VerdictCategory.PARTIAL
        )

        # Partial counts as 0.5
        score = (correct + partial * 0.5) / len(verdicts) * 100
        return round(score, 1)

    def _create_failed_report(
        self, report_id: str, url: str, reason: str
    ) -> AuditReport:
        """Create a failed audit report."""
        return AuditReport(
            report_id=report_id,
            target_url=url,
            total_questions=0,
            verdicts=[],
            summary={"ERROR": 1},
            overall_score=0.0,
            created_at=datetime.utcnow(),
        )

    def _build_system_prompt(self) -> str:
        return """
Jesteś głównym orkiestratorem systemu TruthSeeker Agent.
Twoja rola polega na koordynacji pracy wyspecjalizowanych agentów.
Priorytet: Jakość i dokładność nad szybkością.
"""
