---
name: truthseeker-setup
description: Pełna konfiguracja środowiska TruthSeeker - instalacja zależności, Docker, .env
license: MIT
compatibility: Windows, Docker Desktop, Python 3.11+, uv
metadata:
  author: user
  version: "1.0"
  language: pl
  project: truthseeker
---

Skonfiguruj środowisko TruthSeeker od zera.

**Pre-requisites**
- Docker Desktop zainstalowany i uruchomiony
- Python 3.11+ zainstalowany
- uv zainstalowane (`pip install uv`)

**Steps**

1. **Przejdź do katalogu projektu**
   ```bash
   cd c:\Users\Trzyb\Desktop\truthseeker
   ```

2. **Utwórz plik .env**
   ```bash
   copy .env.example .env
   ```
   
   Uzupełnij wartości w `.env`:
   ```env
   # Wymagane
   OPENAI_API_KEY=sk-...
   
   # Opcjonalne (mają wartości domyślne)
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

3. **Uruchom infrastrukturę Docker**
   ```bash
   docker-compose up -d
   ```
   
   Sprawdź status:
   ```bash
   docker-compose ps
   ```
   
   Oczekiwane kontenery:
   | Kontener | Port | Stan |
   |----------|------|------|
   | qdrant | 6333 | Up |
   | postgres | 5432 | Up |
   | redis | 6379 | Up |

4. **Zainstaluj zależności Python**
   ```bash
   uv sync
   ```

5. **Zainstaluj przeglądarki Playwright**
   ```bash
   uv run playwright install
   ```
   
   Instaluje Chromium, Firefox, WebKit.

6. **Zweryfikuj instalację**
   ```bash
   # Test importów
   uv run python -c "from src.agents.orchestrator import Orchestrator; print('OK')"
   
   # Test Qdrant
   uv run python -c "
   from qdrant_client import QdrantClient
   client = QdrantClient('localhost', port=6333)
   print(f'Qdrant collections: {client.get_collections()}')
   "
   
   # Test OpenAI
   uv run python -c "
   import openai
   import os
   client = openai.OpenAI()
   print('OpenAI API OK')
   "
   ```

7. **Uruchom API**
   ```bash
   uv run python -m src.api.main
   ```
   
   API dostępne na: http://localhost:8000
   Dokumentacja: http://localhost:8000/docs

**Troubleshooting**

| Problem | Komenda diagnostyczna | Rozwiązanie |
|---------|----------------------|-------------|
| Docker nie działa | `docker info` | Uruchom Docker Desktop |
| Port zajęty | `netstat -ano \| findstr :<PORT>` | Zmień port w docker-compose |
| Brak OPENAI_API_KEY | `echo %OPENAI_API_KEY%` | Uzupełnij .env |
| uv nie znaleziony | `pip show uv` | `pip install uv` |

**Output**
Po zakończeniu setupu system jest gotowy do uruchomienia audytu.
Użyj `/audit` lub skill `truthseeker-run-audit` aby rozpocząć.
