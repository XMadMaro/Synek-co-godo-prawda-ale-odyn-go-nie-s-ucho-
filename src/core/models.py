"""
TruthSeeker - Shared Data Models
Pydantic models for data exchange between agents.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class VerdictCategory(str, Enum):
    """Categories for Judge-Dredd verdicts."""
    CORRECT = "POPRAWNA"
    PARTIAL = "CZĘŚCIOWO_POPRAWNA"
    ERROR = "BŁĄD"
    HALLUCINATION = "HALUCYNACJA"
    NO_DATA = "BRAK_DANYCH"


class AgentType(str, Enum):
    """Types of agents in the system."""
    ORCHESTRATOR = "orchestrator"
    SCRAPER_INTEL = "scraper_intel"
    KNOWLEDGE_ARCHITECT = "knowledge_architect"
    CHAT_INTERROGATOR = "chat_interrogator"
    JUDGE_DREDD = "judge_dredd"
    PROMPT_REFINER = "prompt_refiner"


# =============================================================================
# Scraper Models
# =============================================================================

class ScrapedContent(BaseModel):
    """Output from Scraper-Intel agent."""
    url: str
    title: str
    content: str  # Markdown
    content_hash: str
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


# =============================================================================
# RAG / Knowledge Models
# =============================================================================

class TextChunk(BaseModel):
    """A single chunk of text for embedding."""
    id: str
    content: str
    source_url: str
    source_title: str
    position: int  # Position in original document
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexedDocument(BaseModel):
    """Confirmation of document indexing."""
    document_id: str
    chunks_count: int
    vector_ids: list[str]
    indexed_at: datetime = Field(default_factory=datetime.utcnow)


class TestQuestion(BaseModel):
    """A generated test question for Chat-Interrogator."""
    id: str
    question: str
    category: str
    expected_context: str  # What RAG should find
    priority: int = 1  # 1=high, 5=low
    source_url: str | None = None


# =============================================================================
# Interrogation Models
# =============================================================================

class ChatMessage(BaseModel):
    """A single message in chat session."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InterrogationSession(BaseModel):
    """Complete session from Chat-Interrogator."""
    session_id: str
    target_url: str
    persona_name: str
    messages: list[ChatMessage]
    started_at: datetime
    ended_at: datetime
    observations: list[str] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)


class QuestionAnswer(BaseModel):
    """A Q&A pair extracted from session."""
    question_id: str
    question: str
    answer: str
    response_time_ms: int
    timestamp: datetime


# =============================================================================
# Verdict Models
# =============================================================================

class Evidence(BaseModel):
    """Evidence supporting a verdict."""
    source_url: str
    content: str
    relevance_score: float


class Discrepancy(BaseModel):
    """A discrepancy found between chatbot answer and truth."""
    chatbot_claim: str
    truth: str
    explanation: str
    severity: str  # "minor", "major", "critical"


class Verdict(BaseModel):
    """Judge-Dredd's verdict on a single Q&A."""
    question_id: str
    question: str
    chatbot_answer: str
    category: VerdictCategory
    confidence: float = Field(ge=0.0, le=1.0)
    discrepancies: list[Discrepancy] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    explanation: str


class AuditReport(BaseModel):
    """Complete audit report."""
    report_id: str
    target_url: str
    total_questions: int
    verdicts: list[Verdict]
    summary: dict[str, int]  # {"POPRAWNA": 12, "BŁĄD": 3, ...}
    overall_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Prompt Refiner Models
# =============================================================================

class PromptAnalysis(BaseModel):
    """Analysis of errors for prompt improvement."""
    error_patterns: list[str]
    root_causes: list[str]
    recommendations: list[str]


class ImprovedPrompt(BaseModel):
    """Output from Prompt-Refiner agent."""
    original_prompt: str | None
    improved_prompt: str
    changes_summary: list[str]
    analysis: PromptAnalysis
    version: str
