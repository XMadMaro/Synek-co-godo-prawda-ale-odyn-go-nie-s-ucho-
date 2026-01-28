"""
Prompt-Refiner Agent - System Prompt Improvement
Analyzes errors and generates improved chatbot prompts.
"""

from dataclasses import dataclass

from src.agents.base import BaseAgent
from src.core.models import ImprovedPrompt, PromptAnalysis, Verdict


@dataclass
class RefineRequest:
    """Input for Prompt-Refiner agent."""
    verdicts: list[Verdict]
    original_prompt: str | None = None
    chatbot_behavior_description: str | None = None
    context_snippets: list[str] | None = None


class PromptRefinerAgent(BaseAgent[RefineRequest, ImprovedPrompt]):
    """
    Prompt improvement specialist.

    Responsibilities:
    1. Analyze error patterns from Judge-Dredd verdicts
    2. Identify root causes of failures
    3. Generate improved system prompt
    4. Use techniques: Few-Shot, Chain-of-Thought, Negative Constraints
    """

    def __init__(self, llm_client=None):
        super().__init__("prompt_refiner")
        self.llm = llm_client

    async def execute(self, input_data: RefineRequest) -> ImprovedPrompt:
        """
        Analyze errors and generate improved prompt.
        """
        self.log.info(
            "refinement_started",
            verdicts_count=len(input_data.verdicts),
            has_original_prompt=input_data.original_prompt is not None,
        )

        # Step 1: Analyze error patterns
        analysis = await self._analyze_errors(input_data.verdicts)

        # Step 2: Generate improved prompt
        improved = await self._generate_improved_prompt(
            input_data.original_prompt,
            input_data.chatbot_behavior_description,
            analysis,
            input_data.context_snippets or [],
        )

        self.log.info(
            "refinement_completed",
            patterns_found=len(analysis.error_patterns),
            recommendations=len(analysis.recommendations),
        )

        return improved

    async def _analyze_errors(self, verdicts: list[Verdict]) -> PromptAnalysis:
        """
        Analyze error patterns from verdicts.
        """
        error_patterns: list[str] = []
        root_causes: list[str] = []
        recommendations: list[str] = []

        # Group by category
        errors = [v for v in verdicts if v.category.value in ["BŁĄD", "HALUCYNACJA"]]

        if not errors:
            return PromptAnalysis(
                error_patterns=["No significant errors found"],
                root_causes=[],
                recommendations=["Continue monitoring"],
            )

        # Analyze patterns
        # TODO: Use LLM for deeper analysis
        for verdict in errors:
            if verdict.discrepancies:
                for d in verdict.discrepancies:
                    error_patterns.append(
                        f"{d.severity}: {d.chatbot_claim} vs {d.truth}"
                    )

        # Common recommendations based on error types
        hallucinations = [
            v for v in errors if v.category.value == "HALUCYNACJA"
        ]
        if hallucinations:
            root_causes.append("Chatbot generates information not in knowledge base")
            recommendations.append(
                "Add instruction: 'If unsure, say \"I don't have this information\"'"
            )

        return PromptAnalysis(
            error_patterns=error_patterns[:10],  # Limit to top 10
            root_causes=root_causes,
            recommendations=recommendations,
        )

    async def _generate_improved_prompt(
        self,
        original: str | None,
        behavior_desc: str | None,
        analysis: PromptAnalysis,
        context_snippets: list[str],
    ) -> ImprovedPrompt:
        """
        Generate improved system prompt.

        Techniques:
        1. Few-Shot Examples - add correct examples
        2. Negative Constraints - explicit "don't" rules
        3. Chain-of-Thought - reasoning steps
        """
        changes: list[str] = []

        # Build improved prompt
        improved_sections: list[str] = []

        # Base from original or behavior description
        if original:
            improved_sections.append(f"# Rola\n{original}")
        elif behavior_desc:
            improved_sections.append(f"# Rola\n{behavior_desc}")
        else:
            improved_sections.append("# Rola\nJesteś pomocnym asystentem.")

        # Add negative constraints based on errors
        if analysis.recommendations:
            constraints = "\n".join(f"- {r}" for r in analysis.recommendations)
            improved_sections.append(f"\n# WAŻNE ZASADY\n{constraints}")
            changes.append("Added negative constraints based on error analysis")

        # Add few-shot examples from context
        if context_snippets:
            examples = "\n\n".join(
                f"Przykład poprawnej odpowiedzi:\n{s}" for s in context_snippets[:3]
            )
            improved_sections.append(f"\n# Przykłady\n{examples}")
            changes.append("Added few-shot examples from knowledge base")

        # Add reasoning instruction
        if any("HALUCYNACJA" in p for p in analysis.error_patterns):
            improved_sections.append(
                "\n# Proces odpowiedzi\n"
                "1. Sprawdź czy masz odpowiedź w dostępnych danych\n"
                "2. Jeśli nie - powiedz 'nie posiadam tej informacji'\n"
                "3. Nigdy nie wymyślaj odpowiedzi"
            )
            changes.append("Added Chain-of-Thought reasoning instructions")

        return ImprovedPrompt(
            original_prompt=original,
            improved_prompt="\n".join(improved_sections),
            changes_summary=changes,
            analysis=analysis,
            version="1.0",
        )

    def _build_system_prompt(self) -> str:
        return """
Jesteś Prompt-Refiner - ekspertem od poprawy instrukcji systemowych.
Na podstawie analizy błędów generujesz ulepszone prompty.
Techniki: Few-Shot, Chain-of-Thought, Negative Constraints.
Cel: Minimalizacja halucynacji i błędów merytorycznych.
"""
