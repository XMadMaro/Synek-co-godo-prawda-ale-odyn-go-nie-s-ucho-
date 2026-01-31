# Best Practices - TruthSeeker Agent System

## 1. 📁 Struktura Projektu

```
truthseeker/
├── src/
│   ├── agents/                    # Każdy agent jako osobny moduł
│   │   ├── orchestrator/
│   │   ├── scraper_intel/
│   │   ├── knowledge_architect/
│   │   ├── chat_interrogator/
│   │   ├── judge_dredd/
│   │   └── prompt_refiner/
│   ├── core/                      # Współdzielone komponenty
│   │   ├── config.py              # Centralna konfiguracja
│   │   ├── logging.py             # Standaryzowane logowanie
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── models.py              # Pydantic models (shared types)
│   ├── infrastructure/            # Połączenia z bazami/serwisami
│   │   ├── qdrant_client.py
│   │   ├── postgres_client.py
│   │   └── llm_client.py          # OpenAI/Anthropic wrapper
│   └── api/                       # FastAPI endpoints
│       └── routes/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── prompts/                       # Wersjonowane prompty (jak kod!)
│   ├── v1/
│   │   ├── judge_dredd.md
│   │   └── prompt_refiner.md
│   └── v2/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── pyproject.toml                 # UV/Poetry dependencies
├── .env.example
└── README.md
```

### Dlaczego ta struktura?
- **Separacja agentów**: Każdy agent to niezależny moduł, łatwy do testowania.
- **Folder `prompts/`**: Traktuj prompty jak kod - wersjonuj, przeglądaj zmiany!
- **Core/Infrastructure split**: Logika biznesowa oddzielona od szczegółów technicznych.

---

## 2. 🔧 Zarządzanie Konfiguracją

### Hierarchia Konfiguracji:
1. **Defaults** (w kodzie) → 2. **Config file** (YAML) → 3. **.env** (secrets) → 4. **CLI args** (override)

### Przykład z Pydantic Settings:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    postgres_url: str = "postgresql://localhost/truthseeker"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # LLM
    openai_api_key: str  # Required, no default = must be in .env
    llm_model: str = "gpt-4-turbo"
    
    # Agents
    scraper_timeout: int = 30
    judge_confidence_threshold: float = 0.7
    
    class Config:
        env_file = ".env"
        env_prefix = "TS_"  # TS_OPENAI_API_KEY=...
```

### Zasady:
- ✅ **Sekrety TYLKO w .env** (nigdy w kodzie, YAML, repozytorium).
- ✅ **Prefix dla zmiennych** (`TS_`) - unika konfliktów.
- ✅ **Wartości domyślne** dla development, override dla produkcji.

---

## 3. 📝 Wersjonowanie Promptów

### Problem:
Prompty ewoluują. Zmiana jednego słowa może zmienić zachowanie modelu.

### Rozwiązanie:
Traktuj prompty jak kod:
- Przechowuj w `prompts/v1/`, `prompts/v2/`.
- Używaj Git do śledzenia zmian.
- Każda zmiana promptu = nowy commit z opisem.

### Struktura pliku promptu:
```yaml
# prompts/v2/judge_dredd.yaml
metadata:
  version: "2.1"
  author: "Jan Kowalski"
  date: "2026-01-28"
  changelog: "Dodano obsługę kategorii HALUCYNACJA"

system_prompt: |
  Jesteś bezwzględnym sędzią...
  
few_shot_examples:
  - user: "Czy urząd jest czynny w soboty?"
    assistant: |
      Kategoria: BŁĄD
      Uzasadnienie: Chatbot podał "tak", baza wiedzy mówi "nie".
```

---

## 4. 🧪 Strategia Testowania

### Piramida Testów:
```
        /\
       /  \   E2E (Playwright, full pipeline)
      /____\
     /      \  Integration (Agent + Real DB)
    /________\
   /          \ Unit (Logika w izolacji, mocked LLM)
  /______________\
```

### Testowanie Agentów AI:

#### A) Deterministyczne testy (unit):
```python
def test_chunker_splits_correctly():
    text = "Nagłówek\n\nParagraf 1.\n\nParagraf 2."
    chunks = chunker.split(text)
    assert len(chunks) == 2
```

#### B) Testy z mockiem LLM:
```python
@patch("src.infrastructure.llm_client.call_openai")
def test_judge_returns_verdict(mock_llm):
    mock_llm.return_value = '{"verdict": "POPRAWNA", "confidence": 0.9}'
    result = judge.evaluate(question, answer, context)
    assert result.verdict == "POPRAWNA"
```

#### C) Testy ewaluacyjne (Golden Dataset):
Stwórz zbiór pytań z "prawidłowymi" odpowiedziami i mierz accuracy.

```python
def test_judge_accuracy_on_golden_dataset():
    results = [judge.evaluate(q, a, ctx) for q, a, ctx in GOLDEN_DATA]
    accuracy = sum(r.is_correct for r in results) / len(results)
    assert accuracy >= 0.85  # 85% baseline
```

---

## 5. 📊 Obserwability (Logowanie, Metryki)

### Strukturalne Logowanie (JSON):
```python
import structlog

log = structlog.get_logger()

log.info(
    "agent_completed",
    agent="scraper_intel",
    url="https://example.com",
    duration_ms=1234,
    chunks_extracted=15
)
```

Output:
```json
{"event": "agent_completed", "agent": "scraper_intel", "url": "...", "duration_ms": 1234}
```

### Metryki do Śledzenia:
| Metryka | Agent | Opis |
|---------|-------|------|
| `scrape_duration_seconds` | Scraper | Czas pobierania strony |
| `chunks_per_document` | Knowledge | Średnia liczba chunków |
| `llm_tokens_used` | All | Zużycie tokenów (koszty!) |
| `verdict_distribution` | Judge | % POPRAWNA/BŁĄD/HALUCYNACJA |
| `interrogation_success_rate` | Interrogator | % udanych sesji |

---

## 6. 🛡️ Bezpieczeństwo

### Checklist:
- [ ] **Rate Limiting** na API (100 req/min).
- [ ] **Sanityzacja URL** przed scrapowaniem (whitelist domen).
- [ ] **Brak PII** w logach (redakcja PESEL, email).
- [ ] **Timeout** dla wywołań LLM (30s max).
- [ ] **Secrets w .env** (nigdy hardcoded).

### Ochrona przed Injection:
```python
# ❌ ZŁE - user input bezpośrednio w prompcie
prompt = f"Oceń odpowiedź: {user_provided_answer}"

# ✅ DOBRE - strukturyzowane dane
prompt = """
Oceń poniższą odpowiedź:
<answer>
{answer}
</answer>
"""
```

---

## 7. 🔄 CI/CD Pipeline

### GitHub Actions Workflow:
```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
      qdrant:
        image: qdrant/qdrant
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: pip install uv
      - name: Install deps
        run: uv sync
      - name: Lint (Ruff)
        run: uv run ruff check .
      - name: Type check (Pyright)
        run: uv run pyright
      - name: Unit tests
        run: uv run pytest tests/unit
      - name: Integration tests
        run: uv run pytest tests/integration
```

---

## 8. 🏗️ Wzorce Architektoniczne

### A) Dependency Injection:
```python
class JudgeDredd:
    def __init__(self, llm_client: LLMClient, rag_client: RAGClient):
        self.llm = llm_client
        self.rag = rag_client
```
Łatwiejsze testowanie (można wstrzyknąć mocki).

### B) Result Monad (zamiast wyjątków):
```python
from dataclasses import dataclass
from typing import Union

@dataclass
class Success:
    data: dict

@dataclass
class Failure:
    error: str
    code: str

Result = Union[Success, Failure]

def scrape(url: str) -> Result:
    try:
        content = fetch(url)
        return Success(data={"content": content})
    except Timeout:
        return Failure(error="Timeout", code="SCRAPE_TIMEOUT")
```

### C) Event-Driven (dla Orchestratora):
```python
# Orchestrator emituje eventy
events.emit("scrape_completed", {"url": url, "chunks": 15})

# Judge nasłuchuje
@events.on("scrape_completed")
def on_scrape_done(data):
    ...
```

---

## 9. ⚡ Quick Start Template

### Minimalne kroki do uruchomienia:
```bash
# 1. Klonowanie
git clone <repo>
cd truthseeker

# 2. Instalacja
uv sync

# 3. Konfiguracja
cp .env.example .env
# Uzupełnij OPENAI_API_KEY

# 4. Infrastruktura
docker-compose up -d  # Qdrant, Postgres, Redis

# 5. Uruchomienie
uv run python -m src.api.main
```

---

## 10. 📋 Checklist Przed Kodem

Zanim napiszesz pierwszą linijkę, upewnij się że:

- [ ] Masz `.env.example` z wszystkimi wymaganymi zmiennymi.
- [ ] Masz `docker-compose.yml` z Qdrant + Postgres.
- [ ] Masz `pyproject.toml` z zależnościami.
- [ ] Masz folder `prompts/v1/` z pierwszymi wersjami promptów.
- [ ] Masz strukturę folderów jak w sekcji 1.
