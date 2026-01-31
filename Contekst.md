# TruthSeeker - Kontekst Projektu 🧠

> **Ostatnia aktualizacja:** 2026-01-28, 05:58
> **Sesja:** #1

---

## 📋 Aktualny Status

| Aspekt | Status |
|--------|--------|
| **Faza projektu** | MVP - Pełna implementacja agentów |
| **Ocena projektu** | 9.5/10 |
| **Gotowość do uruchomienia** | Tak (wymaga `docker-compose up` + `uv sync`) |

---

## 🏗️ Co zostało zrobione

### Sesja 1 (2026-01-28)

#### Dokumentacja (`c:\Users\Trzyb\Desktop\docs\`)
- [x] `readme.md` - wprowadzenie do projektu
- [x] `architecture.md` - diagram systemu i przepływ danych
- [x] `agents.md` - role i odpowiedzialności 6 agentów
- [x] `truthseeker_prompts.md` - system prompts dla wszystkich agentów
- [x] `best-practices.md` - wytyczne deweloperskie
- [x] `advanced-features.md` - MCP, Skills, Memory, Context Management
- [x] `future-features-spec.md` - Dashboard, A/B Testing, Extension, API, HITL

#### Kod (`c:\Users\Trzyb\Desktop\truthseeker\`)
- [x] Struktura projektu (src/agents, src/core, src/api, src/infrastructure)
- [x] `pyproject.toml` - zależności (FastAPI, Playwright, LangChain, Qdrant)
- [x] `docker-compose.yml` - Qdrant, PostgreSQL, Redis
- [x] `.env.example` - konfiguracja

#### Agenci (PEŁNA IMPLEMENTACJA)
- [x] **Orchestrator** - pipeline 7-fazowy
- [x] **Scraper-Intel** - Playwright + BFS + HTML→Markdown
- [x] **Knowledge-Architect** - LangChain chunking + embeddings + Qdrant
- [x] **Chat-Interrogator** - sesje testowe + edge case detection
- [x] **Judge-Dredd** - RAG + LLM verdicts (5 kategorii)
- [x] **Prompt-Refiner** - analiza błędów + generowanie ulepszeń

#### Infrastruktura
- [x] `LLMClient` - OpenAI + Anthropic (chat, JSON, embeddings)
- [x] `QdrantService` - upsert, search, delete, stats
- [x] FastAPI endpoints (`/health`, `/api/v1/audit`)

---

## 🎯 Następne kroki (do zrobienia)

### Priorytet wysoki
- [ ] Testy jednostkowe dla agentów
- [ ] Uruchomienie i test end-to-end
- [ ] Dodanie brakujących modeli Pydantic (jeśli potrzeba)

### Priorytet średni
- [ ] Dashboard (Next.js) do wizualizacji raportów
- [ ] Integracja z prawdziwym chatbotem (Playwright chat widget)
- [ ] PostgreSQL - persystencja audytów

### Priorytet niski
- [ ] MCP Servers (mcp-server-qdrant, mcp-server-playwright)
- [ ] Skills (.agent/workflows/)
- [ ] Browser Extension
- [ ] API Marketplace

---

## 🔧 Jak uruchomić

```bash
cd c:\Users\Trzyb\Desktop\truthseeker

# 1. Infrastruktura
docker-compose up -d

# 2. Zależności
uv sync
uv run playwright install

# 3. Konfiguracja
copy .env.example .env
# Uzupełnij OPENAI_API_KEY

# 4. Start API
uv run python -m src.api.main
```

---

## 📁 Struktura projektu

```
c:\Users\Trzyb\Desktop\
├── docs\                          # Dokumentacja
│   ├── readme.md
│   ├── architecture.md
│   ├── agents.md
│   ├── truthseeker_prompts.md
│   ├── best-practices.md
│   ├── advanced-features.md
│   ├── future-features-spec.md
│   └── Contekst.md                # ← TEN PLIK
│
└── truthseeker\                   # Kod źródłowy
    ├── src\
    │   ├── agents\                # 6 agentów
    │   ├── core\                  # config, logging, models
    │   ├── api\                   # FastAPI
    │   └── infrastructure\        # LLM + Qdrant clients
    ├── pyproject.toml
    ├── docker-compose.yml
    ├── .env.example
    └── README.md
```

---

## 💡 Ważne decyzje projektowe

1. **Python + FastAPI** - async, szybki development
2. **Qdrant** - vector DB (nie Pinecone, bo self-hosted)
3. **LangChain** - tylko do chunkingu (nie pełny framework)
4. **Playwright** - scraping z JS rendering
5. **Multi-agent** - każdy agent ma jedną odpowiedzialność

---

## 📝 Notatki do następnej sesji

- System jest gotowy do pierwszego testu na żywym chatbocie
- Pamiętaj o API key OpenAI w `.env`
- Rozważ dodanie `pytest` i testów przed demo

---

*Ten plik jest aktualizowany po każdej sesji pracy nad projektem.*
