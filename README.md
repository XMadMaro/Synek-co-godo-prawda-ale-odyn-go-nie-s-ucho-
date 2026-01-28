# TruthSeeker

**AI-powered chatbot auditor and fact-checking system**

TruthSeeker to system wieloagentowy do automatycznego audytu chatbotów. Weryfikuje odpowiedzi chatbotów względem bazy wiedzy (RAG) i generuje raporty jakości.

## 🏗️ Architektura

```
┌──────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
│                   (Główny koordynator)                       │
└──────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│SCRAPER-INTEL │ │  KNOWLEDGE   │ │    CHAT      │ │ JUDGE-DREDD  │
│  (Zbieranie) │ │  ARCHITECT   │ │INTERROGATOR  │ │  (Werdykty)  │
└──────────────┘ │    (RAG)     │ │  (Testy)     │ └──────────────┘
                 └──────────────┘ └──────────────┘        │
                                                          ▼
                                                 ┌──────────────┐
                                                 │PROMPT-REFINER│
                                                 │  (Poprawa)   │
                                                 └──────────────┘
```

## 🚀 Quick Start

```bash
# 1. Klonuj repozytorium
git clone <repo>
cd truthseeker

# 2. Konfiguracja
cp .env.example .env
# Uzupełnij OPENAI_API_KEY w .env

# 3. Uruchom infrastrukturę
docker-compose up -d

# 4. Zainstaluj zależności (używamy uv)
uv sync

# 5. Uruchom API
uv run python -m src.api.main
```

API dostępne pod: `http://localhost:8000/docs`

## 📁 Struktura Projektu

```
truthseeker/
├── src/
│   ├── agents/                 # Agenci AI
│   │   ├── orchestrator/       # Koordynator
│   │   ├── scraper_intel/      # Web scraping
│   │   ├── knowledge_architect/# RAG indexing
│   │   ├── chat_interrogator/  # Testowanie chatbotów
│   │   ├── judge_dredd/        # Weryfikacja
│   │   └── prompt_refiner/     # Poprawa promptów
│   ├── core/                   # Współdzielone
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── models.py
│   └── api/                    # FastAPI
├── docker-compose.yml          # Qdrant, PostgreSQL, Redis
├── pyproject.toml
└── .env.example
```

## 🛠️ Technologie

- **Python 3.11+** + FastAPI
- **OpenAI/Anthropic** - LLM
- **Qdrant** - Vector DB
- **PostgreSQL** - Metadata
- **Redis** - Cache
- **Playwright** - Web scraping

## 📖 Dokumentacja

Pełna dokumentacja w folderze `docs/`:
- `architecture.md` - Diagram systemu
- `agents.md` - Role agentów
- `truthseeker_prompts.md` - System prompts
- `best-practices.md` - Wytyczne deweloperskie
- `advanced-features.md` - MCP, Skills, Memory
- `future-features-spec.md` - Roadmapa

## 📝 Licencja

MIT
