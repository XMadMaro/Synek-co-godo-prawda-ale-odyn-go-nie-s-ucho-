# Antigravity Atomic Tasks - Faza 3: Testy MVP

> **Koordynator**: Claude Opus (Architekt)
> **Executor**: Antigravity Agents + Gemini
> **Cel**: Unit testy dla wszystkich agentow TruthSeeker

---

## Jak uzywac tego pliku

1. Wybierz task z listy ponizej
2. Skopiuj cala sekcje taska do promptu Antigravity
3. Agent wykona task i zwroci rezultat
4. Claude zweryfikuje rezultat przez VerificationAgent
5. Oznacz task jako [x] po pomyslnej weryfikacji

---

## TST-001: Rozbudowa LLMClient Mock

**Status**: [ ] Pending

### Cel
Rozbudowac fixture `mock_llm_client` w conftest.py o wszystkie metody uzywane przez agentow.

### Pliki do przeczytania (kontekst)
```
src/infrastructure/llm_client.py       # Interfejs LLMClient
src/agents/orchestrator/agent.py       # Uzycie chat_json, embed
src/agents/judge_dredd/agent.py        # Uzycie chat_json, chat, embed
tests/conftest.py                      # Obecny stan fixtures
```

### Plik do modyfikacji
```
tests/conftest.py
```

### Instrukcje

1. Otwórz `tests/conftest.py`

2. Znajdź fixture `mock_llm_client()` i rozbuduj go:

```python
@pytest.fixture
def mock_llm_client() -> MagicMock:
    """
    Comprehensive mock LLM client.
    Mocks: chat(), chat_json(), embed()
    """
    mock = MagicMock(spec=LLMClient)

    # Mock chat - returns string
    mock.chat = AsyncMock(return_value="Mock LLM response")

    # Mock chat_json - returns dict
    mock.chat_json = AsyncMock(return_value={
        "passed": True,
        "issues": [],
        "summary": "Code looks good"
    })

    # Mock embed - returns list of embeddings (1536 dims for OpenAI)
    mock.embed = AsyncMock(
        side_effect=lambda texts: [[0.1] * 1536 for _ in texts]
    )

    mock.provider = "mock"
    return mock
```

3. Dodaj wariant dla pytań:

```python
@pytest.fixture
def mock_llm_for_questions() -> MagicMock:
    """LLM mock configured for question generation."""
    mock = MagicMock(spec=LLMClient)
    mock.chat_json = AsyncMock(return_value={
        "questions": [
            {"question": "Jakie sa godziny otwarcia?", "category": "godziny", "priority": 1},
            {"question": "Jak sie skontaktowac?", "category": "kontakt", "priority": 1},
            {"question": "Jakie uslugi oferujecie?", "category": "uslugi", "priority": 2},
        ]
    })
    mock.embed = AsyncMock(return_value=[[0.1] * 1536])
    return mock
```

4. Dodaj wariant dla werdyktów:

```python
@pytest.fixture
def mock_llm_for_judgment() -> MagicMock:
    """LLM mock configured for verdict generation."""
    mock = MagicMock(spec=LLMClient)
    mock.chat_json = AsyncMock(return_value={
        "category": "POPRAWNA",
        "confidence": 0.95,
        "discrepancies": [],
        "explanation": "Odpowiedz zgodna z kontekstem."
    })
    mock.embed = AsyncMock(return_value=[[0.1] * 1536])
    mock.chat = AsyncMock(return_value="Mock response")
    return mock
```

### Oczekiwany rezultat
- Plik `tests/conftest.py` zawiera 3 fixtures dla LLM:
  - `mock_llm_client` - ogólny mock
  - `mock_llm_for_questions` - dla generowania pytań
  - `mock_llm_for_judgment` - dla werdyktów
- Wszystkie metody (chat, chat_json, embed) są AsyncMock

### Weryfikacja
```bash
uv run python -c "from tests.conftest import *; print('OK')"
```

---

## TST-002: Fixture dla QdrantService Mock

**Status**: [ ] Pending

### Cel
Stworzyc fixture `mock_qdrant_service` mockujacy wszystkie operacje wektorowe.

### Pliki do przeczytania (kontekst)
```
src/infrastructure/qdrant_client.py    # Interfejs QdrantService
src/agents/knowledge_architect/agent.py # Uzycie upsert_chunks
src/agents/judge_dredd/agent.py        # Uzycie search
tests/conftest.py                      # Obecny stan fixtures
```

### Plik do modyfikacji
```
tests/conftest.py
```

### Instrukcje

1. Dodaj import na górze pliku:
```python
from src.infrastructure.qdrant_client import QdrantService
from src.core.models import Evidence
```

2. Dodaj fixture:

```python
@pytest.fixture
def mock_qdrant_service() -> MagicMock:
    """
    Comprehensive mock Qdrant service.
    Mocks: ensure_collection, upsert_chunks, search, delete_by_url, get_collection_stats
    """
    mock = MagicMock(spec=QdrantService)

    # ensure_collection - returns True if created
    mock.ensure_collection = AsyncMock(return_value=True)

    # upsert_chunks - returns list of point IDs
    mock.upsert_chunks = AsyncMock(
        side_effect=lambda chunks, embeddings, **kw: [f"pt_{i}" for i in range(len(chunks))]
    )

    # search - returns Evidence list
    mock.search = AsyncMock(return_value=[
        Evidence(
            source_url="https://example.com/page1",
            content="Godziny otwarcia: Pn-Pt 9:00-17:00",
            relevance_score=0.95,
        ),
        Evidence(
            source_url="https://example.com/page2",
            content="Kontakt: tel. 123-456-789",
            relevance_score=0.88,
        ),
    ])

    # delete_by_url
    mock.delete_by_url = AsyncMock(return_value=1)

    # get_collection_stats
    mock.get_collection_stats = AsyncMock(return_value={
        "name": "test_collection",
        "vectors_count": 100,
        "points_count": 100,
        "status": "green",
    })

    mock.default_collection = "knowledge_base"
    return mock
```

3. Dodaj wariant z pustymi wynikami:

```python
@pytest.fixture
def mock_qdrant_empty() -> MagicMock:
    """Qdrant mock returning empty results (NO_DATA scenarios)."""
    mock = MagicMock(spec=QdrantService)
    mock.ensure_collection = AsyncMock(return_value=True)
    mock.search = AsyncMock(return_value=[])
    mock.default_collection = "knowledge_base"
    return mock
```

### Oczekiwany rezultat
- Plik `tests/conftest.py` zawiera 2 fixtures dla Qdrant:
  - `mock_qdrant_service` - zwraca sample data
  - `mock_qdrant_empty` - zwraca puste wyniki

### Weryfikacja
```bash
uv run python -c "from tests.conftest import *; print('OK')"
```

---

## TST-003: Unit testy OrchestratorAgent

**Status**: [ ] Pending

### Cel
Napisac testy jednostkowe dla OrchestratorAgent sprawdzajace pipeline audytu.

### Pliki do przeczytania (kontekst)
```
src/agents/orchestrator/agent.py       # Glowny agent
src/agents/orchestrator/__init__.py    # Exports
src/core/models.py                     # AuditReport, TestQuestion, etc.
tests/conftest.py                      # Fixtures
tests/agents/test_verification.py      # Przyklad struktury testow
```

### Plik do stworzenia
```
tests/agents/test_orchestrator.py
```

### Instrukcje

1. Stworz plik `tests/agents/test_orchestrator.py`:

```python
"""
Tests for OrchestratorAgent - Main coordinator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.agents.orchestrator import OrchestratorAgent, AuditRequest
from src.core.models import (
    AuditReport,
    ScrapedContent,
    IndexedDocument,
    TestQuestion,
    QuestionAnswer,
    Verdict,
    VerdictCategory,
)


class TestOrchestratorAgent:
    """Tests for OrchestratorAgent class."""

    @pytest.fixture
    def orchestrator(self, mock_llm_client, mock_qdrant_service):
        """Create orchestrator with mocked dependencies."""
        agent = OrchestratorAgent(
            llm_client=mock_llm_client,
            qdrant_service=mock_qdrant_service,
        )
        return agent

    @pytest.fixture
    def mock_sub_agents(self, orchestrator):
        """Mock all sub-agents."""
        # Mock ScraperIntelAgent
        orchestrator.scraper.run = AsyncMock(return_value=[
            ScrapedContent(
                url="https://example.com",
                title="Test Page",
                content="# Test Content\nGodziny: 9-17",
                content_hash="abc123",
                scraped_at=datetime.utcnow(),
                metadata={},
            )
        ])

        # Mock KnowledgeArchitectAgent
        orchestrator.knowledge_architect.run = AsyncMock(return_value=[
            IndexedDocument(
                source_url="https://example.com",
                title="Test Page",
                chunks_count=3,
                total_tokens=100,
            )
        ])

        # Mock ChatInterrogatorAgent
        mock_session = MagicMock()
        orchestrator.chat_interrogator.run = AsyncMock(return_value=mock_session)
        orchestrator.chat_interrogator.extract_qa_pairs = MagicMock(return_value=[
            QuestionAnswer(question_id="q1", question="Test?", answer="Yes"),
        ])

        # Mock JudgeDreddAgent
        orchestrator.judge.run = AsyncMock(return_value=[
            Verdict(
                question_id="q1",
                question="Test?",
                chatbot_answer="Yes",
                category=VerdictCategory.CORRECT,
                confidence=0.95,
                explanation="OK",
            )
        ])

        # Mock PromptRefinerAgent
        mock_refine_result = MagicMock()
        mock_refine_result.improved_prompt = "Improved prompt"
        orchestrator.prompt_refiner.run = AsyncMock(return_value=mock_refine_result)

        return orchestrator

    @pytest.mark.asyncio
    async def test_execute_full_pipeline(self, mock_sub_agents):
        """Test full audit pipeline execution."""
        request = AuditRequest(
            target_url="https://example.com",
            scrape_depth=1,
            max_pages=10,
            questions_count=5,
        )

        result = await mock_sub_agents.execute(request)

        assert isinstance(result, AuditReport)
        assert result.target_url == "https://example.com"
        assert result.total_questions == 1
        assert len(result.verdicts) == 1
        assert result.overall_score >= 0

    @pytest.mark.asyncio
    async def test_execute_scraping_failed(self, orchestrator):
        """Test handling of scraping failure."""
        orchestrator.scraper.run = AsyncMock(return_value=[])

        request = AuditRequest(target_url="https://example.com")
        result = await orchestrator.execute(request)

        assert result.overall_score == 0.0
        assert "ERROR" in result.summary

    @pytest.mark.asyncio
    async def test_calculate_score_all_correct(self, orchestrator):
        """Test score calculation with all correct answers."""
        verdicts = [
            Verdict(question_id=f"q{i}", question="?", chatbot_answer="A",
                   category=VerdictCategory.CORRECT, confidence=0.9)
            for i in range(10)
        ]

        score = orchestrator._calculate_score(verdicts)

        assert score == 100.0

    @pytest.mark.asyncio
    async def test_calculate_score_mixed(self, orchestrator):
        """Test score calculation with mixed results."""
        verdicts = [
            Verdict(question_id="q1", question="?", chatbot_answer="A",
                   category=VerdictCategory.CORRECT, confidence=0.9),
            Verdict(question_id="q2", question="?", chatbot_answer="A",
                   category=VerdictCategory.PARTIAL, confidence=0.7),
            Verdict(question_id="q3", question="?", chatbot_answer="A",
                   category=VerdictCategory.ERROR, confidence=0.9),
            Verdict(question_id="q4", question="?", chatbot_answer="A",
                   category=VerdictCategory.HALLUCINATION, confidence=0.9),
        ]

        score = orchestrator._calculate_score(verdicts)

        # 1 correct + 0.5 partial = 1.5 / 4 = 37.5%
        assert score == 37.5

    def test_calculate_summary(self, orchestrator):
        """Test verdict summary calculation."""
        verdicts = [
            Verdict(question_id="q1", question="?", chatbot_answer="A",
                   category=VerdictCategory.CORRECT, confidence=0.9),
            Verdict(question_id="q2", question="?", chatbot_answer="A",
                   category=VerdictCategory.CORRECT, confidence=0.9),
            Verdict(question_id="q3", question="?", chatbot_answer="A",
                   category=VerdictCategory.ERROR, confidence=0.9),
        ]

        summary = orchestrator._calculate_summary(verdicts)

        assert summary["POPRAWNA"] == 2
        assert summary["BLAD"] == 1


class TestAuditRequest:
    """Tests for AuditRequest dataclass."""

    def test_audit_request_defaults(self):
        """Test AuditRequest default values."""
        request = AuditRequest(target_url="https://example.com")

        assert request.scrape_depth == 2
        assert request.max_pages == 50
        assert request.questions_count == 20
        assert request.generate_prompt_improvement is True

    def test_audit_request_custom(self):
        """Test AuditRequest with custom values."""
        request = AuditRequest(
            target_url="https://test.com",
            scrape_depth=3,
            max_pages=100,
            questions_count=50,
            collection_name="custom_kb",
        )

        assert request.scrape_depth == 3
        assert request.collection_name == "custom_kb"
```

### Oczekiwany rezultat
- Plik `tests/agents/test_orchestrator.py` z 7+ testami
- Testy pokrywaja: pipeline, scoring, summary, error handling

### Weryfikacja
```bash
uv run pytest tests/agents/test_orchestrator.py -v
```

---

## TST-004: Unit testy ScraperIntelAgent

**Status**: [ ] Pending

### Cel
Napisac testy jednostkowe dla ScraperIntelAgent sprawdzajace scraping i parsing.

### Pliki do przeczytania (kontekst)
```
src/agents/scraper_intel/agent.py      # Agent scraper
src/core/models.py                     # ScrapedContent
tests/conftest.py                      # Fixtures
```

### Plik do stworzenia
```
tests/agents/test_scraper.py
```

### Instrukcje

1. Stworz plik `tests/agents/test_scraper.py`:

```python
"""
Tests for ScraperIntelAgent - Web intelligence gathering.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.agents.scraper_intel import ScraperIntelAgent, ScrapeRequest
from src.core.models import ScrapedContent


class TestScraperIntelAgent:
    """Tests for ScraperIntelAgent class."""

    @pytest.fixture
    def scraper(self):
        """Create scraper agent."""
        return ScraperIntelAgent()

    def test_should_exclude_images(self, scraper):
        """Test URL exclusion for image files."""
        assert scraper._should_exclude("https://example.com/image.jpg",
                                       scraper._get_default_exclude_patterns()) is True
        assert scraper._should_exclude("https://example.com/photo.PNG",
                                       scraper._get_default_exclude_patterns()) is True

    def test_should_exclude_admin(self, scraper):
        """Test URL exclusion for admin pages."""
        patterns = [r".*/admin.*", r".*/login.*"]
        assert scraper._should_exclude("https://example.com/admin/panel", patterns) is True
        assert scraper._should_exclude("https://example.com/login", patterns) is True

    def test_should_not_exclude_content(self, scraper):
        """Test valid URLs are not excluded."""
        patterns = [r".*\.(jpg|png)$", r".*/admin.*"]
        assert scraper._should_exclude("https://example.com/about", patterns) is False
        assert scraper._should_exclude("https://example.com/contact", patterns) is False

    def test_html_to_markdown_basic(self, scraper):
        """Test HTML to Markdown conversion."""
        html = """
        <html>
        <body>
            <main>
                <h1>Title</h1>
                <p>Some paragraph text.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </main>
        </body>
        </html>
        """

        md = scraper._html_to_markdown(html)

        assert "# Title" in md
        assert "Some paragraph text" in md
        assert "- Item 1" in md or "Item 1" in md

    def test_html_to_markdown_removes_nav(self, scraper):
        """Test that navigation elements are removed."""
        html = """
        <html>
        <body>
            <nav>Navigation menu</nav>
            <main><p>Main content</p></main>
            <footer>Footer info</footer>
        </body>
        </html>
        """

        md = scraper._html_to_markdown(html)

        assert "Navigation menu" not in md
        assert "Footer info" not in md
        assert "Main content" in md

    def test_html_to_markdown_table(self, scraper):
        """Test table conversion to Markdown."""
        html = """
        <main>
        <table>
            <tr><th>Col1</th><th>Col2</th></tr>
            <tr><td>A</td><td>B</td></tr>
            <tr><td>C</td><td>D</td></tr>
        </table>
        </main>
        """

        md = scraper._html_to_markdown(html)

        assert "Col1" in md
        assert "|" in md  # Markdown table syntax

    @pytest.mark.asyncio
    async def test_execute_with_mock_playwright(self, scraper):
        """Test execute with mocked Playwright."""
        # This test requires mocking playwright
        # For now, test the request validation
        request = ScrapeRequest(
            url="https://example.com",
            depth=1,
            max_pages=5,
        )

        assert request.url == "https://example.com"
        assert request.depth == 1
        assert request.max_pages == 5


class TestScrapeRequest:
    """Tests for ScrapeRequest dataclass."""

    def test_scrape_request_defaults(self):
        """Test ScrapeRequest default values."""
        request = ScrapeRequest(url="https://example.com")

        assert request.depth == 2
        assert request.max_pages == 50
        assert request.wait_for_js is True
        assert len(request.exclude_patterns) > 0

    def test_scrape_request_custom(self):
        """Test ScrapeRequest with custom values."""
        request = ScrapeRequest(
            url="https://test.com",
            depth=3,
            max_pages=100,
            wait_for_js=False,
            include_patterns=[r".*/docs/.*"],
        )

        assert request.depth == 3
        assert request.wait_for_js is False
        assert r".*/docs/.*" in request.include_patterns
```

### Oczekiwany rezultat
- Plik `tests/agents/test_scraper.py` z 8+ testami
- Testy pokrywaja: URL exclusion, HTML parsing, Markdown conversion

### Weryfikacja
```bash
uv run pytest tests/agents/test_scraper.py -v
```

---

## TST-005: Unit testy JudgeDreddAgent

**Status**: [ ] Pending

### Cel
Napisac testy jednostkowe dla JudgeDreddAgent sprawdzajace ewaluacje odpowiedzi.

### Pliki do przeczytania (kontekst)
```
src/agents/judge_dredd/agent.py        # Agent Judge
src/core/models.py                     # Verdict, VerdictCategory, Evidence
tests/conftest.py                      # Fixtures
```

### Plik do stworzenia
```
tests/agents/test_judge.py
```

### Instrukcje

1. Stworz plik `tests/agents/test_judge.py`:

```python
"""
Tests for JudgeDreddAgent - Verdict generator.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.judge_dredd import JudgeDreddAgent, JudgeInput
from src.core.models import (
    QuestionAnswer,
    Verdict,
    VerdictCategory,
    Evidence,
)


class TestJudgeDreddAgent:
    """Tests for JudgeDreddAgent class."""

    @pytest.fixture
    def judge(self, mock_llm_for_judgment, mock_qdrant_service):
        """Create judge agent with mocked dependencies."""
        return JudgeDreddAgent(
            llm_client=mock_llm_for_judgment,
            qdrant_service=mock_qdrant_service,
        )

    @pytest.fixture
    def sample_qa_pairs(self):
        """Sample Q&A pairs for testing."""
        return [
            QuestionAnswer(
                question_id="q1",
                question="Jakie sa godziny otwarcia?",
                answer="Jestesmy otwarci 9:00-17:00.",
            ),
            QuestionAnswer(
                question_id="q2",
                question="Jaki jest telefon kontaktowy?",
                answer="123-456-789",
            ),
        ]

    @pytest.mark.asyncio
    async def test_execute_returns_verdicts(self, judge, sample_qa_pairs):
        """Test that execute returns verdict for each Q&A pair."""
        input_data = JudgeInput(
            qa_pairs=sample_qa_pairs,
            rag_collection="test_kb",
        )

        verdicts = await judge.execute(input_data)

        assert len(verdicts) == 2
        assert all(isinstance(v, Verdict) for v in verdicts)

    @pytest.mark.asyncio
    async def test_execute_correct_verdict(self, judge, mock_llm_for_judgment):
        """Test verdict generation for correct answer."""
        mock_llm_for_judgment.chat_json = AsyncMock(return_value={
            "category": "POPRAWNA",
            "confidence": 0.95,
            "discrepancies": [],
            "explanation": "Odpowiedz zgodna z kontekstem.",
        })

        qa = [QuestionAnswer(question_id="q1", question="Test?", answer="Yes")]
        result = await judge.execute(JudgeInput(qa_pairs=qa))

        assert result[0].category == VerdictCategory.CORRECT
        assert result[0].confidence == 0.95

    @pytest.mark.asyncio
    async def test_execute_error_verdict(self, judge, mock_llm_for_judgment):
        """Test verdict generation for incorrect answer."""
        mock_llm_for_judgment.chat_json = AsyncMock(return_value={
            "category": "BLAD",
            "confidence": 0.90,
            "discrepancies": [
                {"chatbot_claim": "150 PLN", "truth": "200 PLN", "severity": "major"}
            ],
            "explanation": "Bledna cena.",
        })

        qa = [QuestionAnswer(question_id="q1", question="Cena?", answer="150 PLN")]
        result = await judge.execute(JudgeInput(qa_pairs=qa))

        assert result[0].category == VerdictCategory.ERROR
        assert len(result[0].discrepancies) == 1

    @pytest.mark.asyncio
    async def test_execute_no_data_empty_rag(self, judge, mock_qdrant_empty, mock_llm_for_judgment):
        """Test verdict when RAG returns no results."""
        judge.qdrant = mock_qdrant_empty
        mock_llm_for_judgment.chat_json = AsyncMock(return_value={
            "category": "BRAK_DANYCH",
            "confidence": 0.3,
            "discrepancies": [],
            "explanation": "Brak kontekstu do oceny.",
        })

        qa = [QuestionAnswer(question_id="q1", question="Unknown?", answer="Maybe")]
        result = await judge.execute(JudgeInput(qa_pairs=qa))

        assert result[0].category == VerdictCategory.NO_DATA

    def test_build_evaluation_messages(self, judge):
        """Test evaluation prompt building."""
        qa = QuestionAnswer(question_id="q1", question="Test?", answer="Yes")
        evidence = [
            Evidence(source_url="https://ex.com", content="Test content", relevance_score=0.9)
        ]

        messages = judge._build_evaluation_messages(qa, evidence)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Test?" in messages[1]["content"]
        assert "Yes" in messages[1]["content"]
        assert "Test content" in messages[1]["content"]

    def test_summarize_verdicts(self, judge):
        """Test verdict summary generation."""
        verdicts = [
            Verdict(question_id="q1", question="?", chatbot_answer="A",
                   category=VerdictCategory.CORRECT, confidence=0.9),
            Verdict(question_id="q2", question="?", chatbot_answer="A",
                   category=VerdictCategory.CORRECT, confidence=0.8),
            Verdict(question_id="q3", question="?", chatbot_answer="A",
                   category=VerdictCategory.ERROR, confidence=0.9),
        ]

        summary = judge._summarize_verdicts(verdicts)

        assert summary["total"] == 3
        assert summary["distribution"]["POPRAWNA"] == 2
        assert summary["distribution"]["BLAD"] == 1
        assert summary["accuracy"] == pytest.approx(66.7, rel=0.1)

    def test_parse_text_response_json(self, judge):
        """Test fallback JSON parsing from text."""
        text = 'Some text {"category": "POPRAWNA", "confidence": 0.8} more text'

        result = judge._parse_text_response(text)

        assert result["category"] == "POPRAWNA"
        assert result["confidence"] == 0.8

    def test_parse_text_response_fallback(self, judge):
        """Test fallback when no JSON found."""
        text = "No JSON here at all"

        result = judge._parse_text_response(text)

        assert result["category"] == "BRAK_DANYCH"
        assert result["confidence"] == 0.3


class TestJudgeInput:
    """Tests for JudgeInput dataclass."""

    def test_judge_input_defaults(self):
        """Test JudgeInput default values."""
        qa = [QuestionAnswer(question_id="q1", question="?", answer="!")]
        input_data = JudgeInput(qa_pairs=qa)

        assert input_data.rag_collection == "knowledge_base"
        assert input_data.top_k == 5
        assert input_data.use_anthropic is False

    def test_judge_input_custom(self):
        """Test JudgeInput with custom values."""
        qa = [QuestionAnswer(question_id="q1", question="?", answer="!")]
        input_data = JudgeInput(
            qa_pairs=qa,
            rag_collection="custom_kb",
            top_k=10,
            use_anthropic=True,
        )

        assert input_data.rag_collection == "custom_kb"
        assert input_data.top_k == 10
        assert input_data.use_anthropic is True
```

### Oczekiwany rezultat
- Plik `tests/agents/test_judge.py` z 10+ testami
- Testy pokrywaja: verdict generation, categories, RAG integration, parsing

### Weryfikacja
```bash
uv run pytest tests/agents/test_judge.py -v
```

---

## TST-006: Integration Test - Full Pipeline

**Status**: [ ] Pending

### Cel
Napisac test integracyjny sprawdzajacy caly pipeline audytu end-to-end.

### Pliki do przeczytania (kontekst)
```
src/agents/orchestrator/agent.py       # Glowny pipeline
src/agents/*/agent.py                  # Wszystkie agenty
tests/conftest.py                      # Fixtures
```

### Plik do stworzenia
```
tests/integration/test_pipeline.py
```

### Instrukcje

1. Stworz folder `tests/integration/` jesli nie istnieje

2. Stworz `tests/integration/__init__.py`:
```python
"""Integration tests package."""
```

3. Stworz `tests/integration/test_pipeline.py`:

```python
"""
Integration tests for full TruthSeeker pipeline.
Tests the complete audit flow with mocked external services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.agents.orchestrator import OrchestratorAgent, AuditRequest
from src.core.models import (
    AuditReport,
    ScrapedContent,
    IndexedDocument,
    QuestionAnswer,
    Verdict,
    VerdictCategory,
    ChatSession,
)


class TestFullPipeline:
    """End-to-end integration tests."""

    @pytest.fixture
    def fully_mocked_orchestrator(self, mock_llm_client, mock_qdrant_service):
        """Create orchestrator with all dependencies mocked."""
        agent = OrchestratorAgent(
            llm_client=mock_llm_client,
            qdrant_service=mock_qdrant_service,
        )

        # Mock Scraper
        agent.scraper.run = AsyncMock(return_value=[
            ScrapedContent(
                url="https://example.com",
                title="Example Page",
                content="# Example\nGodziny: 9-17\nTelefon: 123-456-789",
                content_hash="hash123",
                scraped_at=datetime.utcnow(),
                metadata={"status_code": 200},
            ),
            ScrapedContent(
                url="https://example.com/services",
                title="Services",
                content="# Uslugi\nKonsultacje: 200 PLN/h",
                content_hash="hash456",
                scraped_at=datetime.utcnow(),
                metadata={"status_code": 200},
            ),
        ])

        # Mock Knowledge Architect
        agent.knowledge_architect.run = AsyncMock(return_value=[
            IndexedDocument(source_url="https://example.com", title="Example", chunks_count=5, total_tokens=200),
            IndexedDocument(source_url="https://example.com/services", title="Services", chunks_count=3, total_tokens=100),
        ])

        # Mock Chat Interrogator
        mock_session = MagicMock()
        agent.chat_interrogator.run = AsyncMock(return_value=mock_session)
        agent.chat_interrogator.extract_qa_pairs = MagicMock(return_value=[
            QuestionAnswer(question_id="q1", question="Godziny?", answer="9-17"),
            QuestionAnswer(question_id="q2", question="Telefon?", answer="123-456-789"),
            QuestionAnswer(question_id="q3", question="Cena konsultacji?", answer="150 PLN"),  # WRONG!
        ])

        # Mock Judge
        agent.judge.run = AsyncMock(return_value=[
            Verdict(question_id="q1", question="Godziny?", chatbot_answer="9-17",
                   category=VerdictCategory.CORRECT, confidence=0.95, explanation="OK"),
            Verdict(question_id="q2", question="Telefon?", chatbot_answer="123-456-789",
                   category=VerdictCategory.CORRECT, confidence=0.98, explanation="OK"),
            Verdict(question_id="q3", question="Cena?", chatbot_answer="150 PLN",
                   category=VerdictCategory.ERROR, confidence=0.92, explanation="Bledna cena"),
        ])

        # Mock Prompt Refiner
        mock_refine = MagicMock()
        mock_refine.improved_prompt = "Upewnij sie ze podajesz prawidlowe ceny."
        agent.prompt_refiner.run = AsyncMock(return_value=mock_refine)

        return agent

    @pytest.mark.asyncio
    async def test_full_audit_pipeline(self, fully_mocked_orchestrator):
        """Test complete audit from URL to report."""
        request = AuditRequest(
            target_url="https://example.com",
            scrape_depth=2,
            max_pages=10,
            questions_count=5,
            generate_prompt_improvement=True,
        )

        report = await fully_mocked_orchestrator.execute(request)

        # Verify report structure
        assert isinstance(report, AuditReport)
        assert report.target_url == "https://example.com"
        assert report.report_id.startswith("audit_")

        # Verify all phases executed
        fully_mocked_orchestrator.scraper.run.assert_called_once()
        fully_mocked_orchestrator.knowledge_architect.run.assert_called_once()
        fully_mocked_orchestrator.chat_interrogator.run.assert_called_once()
        fully_mocked_orchestrator.judge.run.assert_called_once()

        # Verify verdicts
        assert report.total_questions == 3
        assert len(report.verdicts) == 3

        # Verify scoring (2 correct, 1 error = 66.7%)
        assert report.overall_score == pytest.approx(66.7, rel=0.1)

        # Verify summary
        assert report.summary["POPRAWNA"] == 2
        assert report.summary["BLAD"] == 1

    @pytest.mark.asyncio
    async def test_pipeline_handles_scraper_failure(self, fully_mocked_orchestrator):
        """Test pipeline gracefully handles scraper returning no content."""
        fully_mocked_orchestrator.scraper.run = AsyncMock(return_value=[])

        request = AuditRequest(target_url="https://broken.com")
        report = await fully_mocked_orchestrator.execute(request)

        assert report.overall_score == 0.0
        assert "ERROR" in report.summary

    @pytest.mark.asyncio
    async def test_pipeline_without_prompt_improvement(self, fully_mocked_orchestrator):
        """Test pipeline skips prompt improvement when disabled."""
        request = AuditRequest(
            target_url="https://example.com",
            generate_prompt_improvement=False,
        )

        report = await fully_mocked_orchestrator.execute(request)

        # Prompt refiner should not be called
        fully_mocked_orchestrator.prompt_refiner.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_pipeline_custom_collection(self, fully_mocked_orchestrator):
        """Test pipeline uses custom collection name."""
        request = AuditRequest(
            target_url="https://example.com",
            collection_name="my_custom_kb",
        )

        await fully_mocked_orchestrator.execute(request)

        # Verify collection name passed to knowledge architect
        call_args = fully_mocked_orchestrator.knowledge_architect.run.call_args
        assert call_args[0][0].collection_name == "my_custom_kb"


class TestPipelinePerformance:
    """Performance-related tests."""

    @pytest.mark.asyncio
    async def test_report_has_timing_info(self, fully_mocked_orchestrator):
        """Test that report includes timing metadata."""
        request = AuditRequest(target_url="https://example.com")
        report = await fully_mocked_orchestrator.execute(request)

        # Report should have creation timestamp
        assert report.created_at is not None
        assert isinstance(report.created_at, datetime)
```

### Oczekiwany rezultat
- Folder `tests/integration/` z plikiem `__init__.py`
- Plik `tests/integration/test_pipeline.py` z 5+ testami
- Testy pokrywaja: full pipeline, error handling, config options

### Weryfikacja
```bash
uv run pytest tests/integration/test_pipeline.py -v
```

---

## Checklist Fazy 3

Po zakonczeniu wszystkich taskow:

```bash
# Uruchom wszystkie testy
uv run pytest tests/ -v --tb=short

# Sprawdz coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Sprawdz typy
uv run mypy src/

# Sprawdz lint
uv run ruff check src/ tests/
```

### Kryteria sukcesu
- [ ] Wszystkie testy przechodza (pytest exit code 0)
- [ ] Coverage > 60% dla agentow
- [ ] Brak bledow mypy
- [ ] Brak bledow ruff

---

## Notatki dla agentow Antigravity

1. **Kontekst**: Zawsze czytaj pliki z sekcji "Pliki do przeczytania" przed implementacja
2. **Imports**: Sprawdz istniejace importy w `conftest.py` przed dodaniem nowych
3. **AsyncMock**: Uzywaj `AsyncMock` dla wszystkich metod async
4. **VerdictCategory**: Enum values to polskie nazwy (`POPRAWNA`, `BLAD`, etc.)
5. **Fixtures**: Uzywaj istniejacych fixtures zamiast tworzenia nowych mockow
6. **Weryfikacja**: Po zakonczeniu taska, uruchom polecenie z sekcji "Weryfikacja"
