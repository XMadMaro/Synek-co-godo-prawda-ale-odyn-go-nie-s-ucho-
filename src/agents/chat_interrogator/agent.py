"""
Chat-Interrogator Agent - Chatbot Testing
Conducts interactive conversations with target chatbots.
"""

from dataclasses import dataclass
from datetime import datetime

from src.agents.base import BaseAgent
from src.core.models import (
    ChatMessage,
    InterrogationSession,
    QuestionAnswer,
    TestQuestion,
)


@dataclass
class InterrogateRequest:
    """Input for Chat-Interrogator agent."""
    target_url: str
    questions: list[TestQuestion]
    chat_selector: str | None = None  # CSS selector for chat widget
    wait_between_messages: int = 2


class ChatInterrogatorAgent(BaseAgent[InterrogateRequest, InterrogationSession]):
    """
    Chatbot testing agent using Playwright.

    Responsibilities:
    1. Navigate to target URL
    2. Locate chat widget (auto-detect or via selector)
    3. Conduct interrogation using test questions
    4. Record all responses with timing
    5. Detect edge cases and anomalies
    """

    def __init__(self, browser=None):
        super().__init__("chat_interrogator")
        self.browser = browser

    async def execute(self, input_data: InterrogateRequest) -> InterrogationSession:
        """
        Conduct interrogation session.
        """
        session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow()

        self.log.info(
            "interrogation_started",
            session_id=session_id,
            target_url=input_data.target_url,
            questions_count=len(input_data.questions),
        )

        messages: list[ChatMessage] = []
        observations: list[str] = []
        edge_cases: list[str] = []

        # TODO: Implement with Playwright
        # 1. Navigate to target URL
        # 2. Find and interact with chat widget
        # 3. Send questions and capture responses

        for question in input_data.questions:
            try:
                # Send question
                messages.append(
                    ChatMessage(role="user", content=question.question)
                )

                # TODO: Get response from chatbot
                response = await self._get_chatbot_response(question.question)

                messages.append(
                    ChatMessage(role="assistant", content=response or "No response")
                )

                # Detect edge cases
                if await self._detect_edge_case(question.question, response):
                    edge_cases.append(question.question)

            except Exception as e:
                self.log.warning(
                    "question_failed",
                    question=question.question,
                    error=str(e),
                )
                observations.append(f"Failed: {question.question} - {e}")

        ended_at = datetime.utcnow()

        session = InterrogationSession(
            session_id=session_id,
            target_url=input_data.target_url,
            persona_name="Standard Interrogator",
            messages=messages,
            started_at=started_at,
            ended_at=ended_at,
            observations=observations,
            edge_cases=edge_cases,
        )

        self.log.info(
            "interrogation_completed",
            session_id=session_id,
            messages_count=len(messages),
            edge_cases_count=len(edge_cases),
        )

        return session

    async def _get_chatbot_response(self, question: str) -> str | None:
        """Get response from chatbot. TODO: Implement with Playwright."""
        return None

    async def _detect_edge_case(self, question: str, response: str | None) -> bool:
        """Detect if response is an edge case (error, refusal, etc.)."""
        if not response:
            return True
        edge_indicators = [
            "nie rozumiem",
            "nie wiem",
            "przepraszam",
            "błąd",
            "error",
        ]
        return any(ind in response.lower() for ind in edge_indicators)

    def extract_qa_pairs(self, session: InterrogationSession) -> list[QuestionAnswer]:
        """Extract Q&A pairs from session for Judge-Dredd."""
        pairs: list[QuestionAnswer] = []
        idx = 0

        for i in range(0, len(session.messages) - 1, 2):
            if (
                session.messages[i].role == "user"
                and session.messages[i + 1].role == "assistant"
            ):
                pairs.append(
                    QuestionAnswer(
                        question_id=f"{session.session_id}_{idx}",
                        question=session.messages[i].content,
                        answer=session.messages[i + 1].content,
                        response_time_ms=0,  # TODO: Calculate
                        timestamp=session.messages[i + 1].timestamp,
                    )
                )
                idx += 1

        return pairs

    def _build_system_prompt(self) -> str:
        return """
Jesteś Chat-Interrogator - przesłuchujesz chatboty w poszukiwaniu słabości.
Zadawaj pytania naturalnie, jak zwykły użytkownik.
Obserwuj: opóźnienia, puste odpowiedzi, powtórzenia, błędy.
Raportuj wszystkie anomalie.
"""
