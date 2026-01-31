---
name: truthseeker-debug
description: Debuguj problemy w TruthSeeker - sprawdź logi, infrastrukturę, połączenia
license: MIT
compatibility: Windows, Docker
metadata:
  author: user
  version: "1.0"
  language: pl
  project: truthseeker
---

Debuguj problemy w systemie TruthSeeker.

**Input**: Opis problemu lub symptom (np. "API nie odpowiada", "Qdrant timeout")

**Steps**

1. **Zidentyfikuj kategorię problemu**

   | Symptom | Kategoria | Przejdź do |
   |---------|-----------|------------|
   | API nie startuje | Aplikacja | Krok 2 |
   | Timeout / 500 | Infrastruktura | Krok 3 |
   | Błąd OpenAI | Zewnętrzne API | Krok 4 |
   | Playwright error | Scraping | Krok 5 |
   | Puste wyniki RAG | Qdrant | Krok 6 |

2. **Debug Aplikacji**
   
   Sprawdź logi:
   ```bash
   cd c:\Users\Trzyb\Desktop\truthseeker
   uv run python -m src.api.main 2>&1 | tee debug.log
   ```
   
   Sprawdź importy:
   ```bash
   uv run python -c "
   import sys
   sys.path.insert(0, '.')
   from src.agents.orchestrator import Orchestrator
   from src.infrastructure.llm_client import LLMClient
   from src.infrastructure.qdrant_service import QdrantService
   print('Wszystkie importy OK')
   "
   ```
   
   Typowe problemy:
   - `ModuleNotFoundError` → `uv sync`
   - `ImportError` → sprawdź ścieżki w `__init__.py`

3. **Debug Infrastruktury**
   
   Status kontenerów:
   ```bash
   docker-compose ps
   docker-compose logs --tail=50
   ```
   
   Test połączeń:
   ```bash
   # Qdrant
   curl http://localhost:6333/collections
   
   # PostgreSQL
   docker exec -it truthseeker-postgres-1 psql -U postgres -c "SELECT 1"
   
   # Redis
   docker exec -it truthseeker-redis-1 redis-cli ping
   ```
   
   Restart infrastruktury:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Debug OpenAI API**
   
   Test połączenia:
   ```bash
   uv run python -c "
   import openai
   import os
   
   client = openai.OpenAI()
   response = client.chat.completions.create(
       model='gpt-4o-mini',
       messages=[{'role': 'user', 'content': 'test'}],
       max_tokens=5
   )
   print(f'API OK: {response.choices[0].message.content}')
   "
   ```
   
   Typowe błędy:
   | Błąd | Przyczyna | Rozwiązanie |
   |------|-----------|-------------|
   | AuthenticationError | Zły klucz | Sprawdź OPENAI_API_KEY |
   | RateLimitError | Limit | Poczekaj lub upgrade planu |
   | Timeout | Sieć | Sprawdź proxy/firewall |

5. **Debug Playwright/Scraping**
   
   Test przeglądarki:
   ```bash
   uv run python -c "
   import asyncio
   from playwright.async_api import async_playwright
   
   async def test():
       async with async_playwright() as p:
           browser = await p.chromium.launch(headless=True)
           page = await browser.new_page()
           await page.goto('https://example.com')
           print(f'Title: {await page.title()}')
           await browser.close()
   
   asyncio.run(test())
   "
   ```
   
   Jeśli błąd:
   ```bash
   uv run playwright install
   uv run playwright install-deps  # Linux/WSL
   ```

6. **Debug Qdrant/RAG**
   
   Sprawdź kolekcje:
   ```bash
   curl http://localhost:6333/collections | python -m json.tool
   ```
   
   Sprawdź zawartość kolekcji:
   ```bash
   uv run python -c "
   from qdrant_client import QdrantClient
   
   client = QdrantClient('localhost', port=6333)
   collections = client.get_collections().collections
   
   for col in collections:
       info = client.get_collection(col.name)
       print(f'{col.name}: {info.points_count} punktów')
   "
   ```
   
   Reset kolekcji (UWAGA: usuwa dane!):
   ```bash
   curl -X DELETE http://localhost:6333/collections/<nazwa>
   ```

7. **Generuj raport debugowania**
   
   Zbierz wszystkie informacje:
   ```bash
   echo "=== SYSTEM INFO ===" > debug-report.txt
   python --version >> debug-report.txt
   docker --version >> debug-report.txt
   
   echo "=== DOCKER ===" >> debug-report.txt
   docker-compose ps >> debug-report.txt
   
   echo "=== QDRANT ===" >> debug-report.txt
   curl -s http://localhost:6333/collections >> debug-report.txt
   
   echo "=== ENV ===" >> debug-report.txt
   type .env | findstr /V "KEY\|SECRET\|PASSWORD" >> debug-report.txt
   ```

**Output**
Po zidentyfikowaniu problemu:
1. Opisz przyczynę
2. Podaj rozwiązanie
3. Zweryfikuj naprawę
