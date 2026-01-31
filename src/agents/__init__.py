"""TruthSeeker Agents Package."""

from src.agents.chat_interrogator import ChatInterrogatorAgent, InterrogateRequest
from src.agents.judge_dredd import JudgeDreddAgent, JudgeInput
from src.agents.knowledge_architect import IndexRequest, KnowledgeArchitectAgent
from src.agents.orchestrator import AuditRequest, OrchestratorAgent
from src.agents.prompt_refiner import PromptRefinerAgent, RefineRequest
from src.agents.scraper_intel import ScraperIntelAgent, ScrapeRequest
from src.agents.verification import VerificationAgent

__all__ = [
    # Agents
    "OrchestratorAgent",
    "ScraperIntelAgent",
    "KnowledgeArchitectAgent",
    "ChatInterrogatorAgent",
    "JudgeDreddAgent",
    "PromptRefinerAgent",
    "VerificationAgent",
    # Request types
    "AuditRequest",
    "ScrapeRequest",
    "IndexRequest",
    "InterrogateRequest",
    "JudgeInput",
    "RefineRequest",
]
