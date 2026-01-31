---
name: truthseeker-test-agent
description: Testuj pojedynczego agenta TruthSeeker w izolacji - przydatne do debugowania i rozwoju
license: MIT
compatibility: Python 3.11+, uv
metadata:
  author: user
  version: "1.0"
  language: pl
  project: truthseeker
---

Testuj pojedynczego agenta TruthSeeker w izolacji.

**Input**: Nazwa agenta do testowania (scraper-intel, knowledge-architect, chat-interrogator, judge-dredd, prompt-refiner)

**Steps**

1. **Wybierz agenta do testu**

   Dostępni agenci:
   | Agent | Odpowiedzialność | Wymagania |
   |-------|------------------|-----------|
   | `scraper-intel` | Pobieranie treści stron | Playwright |
   | `knowledge-architect` | Indeksowanie do Qdrant | Qdrant, OpenAI |
   | `chat-interrogator` | Testowanie chatbotów | Playwright |
   | `judge-dredd` | Weryfikacja odpowiedzi | Qdrant, OpenAI |
   | `prompt-refiner` | Ulepszanie promptów | OpenAI |

2. **Przygotuj dane testowe**

   Dla każdego agenta przygotuj odpowiednie dane wejściowe:

   ### scraper-intel
   ```python
   from src.agents.scraper_intel import ScraperIntel
   
   scraper = ScraperIntel()
   result = await scraper.scrape("https://example.com")
   print(result.content)
   ```

   ### knowledge-architect
   ```python
   from src.agents.knowledge_architect import KnowledgeArchitect
   
   architect = KnowledgeArchitect()
   result = await architect.index_document(
       content="Treść dokumentu...",
       source_url="https://example.com",
       title="Przykładowy dokument"
   )
   print(f"Zaindeksowano {result.chunk_count} fragmentów")
   ```

   ### chat-interrogator
   ```python
   from src.agents.chat_interrogator import ChatInterrogator
   
   interrogator = ChatInterrogator()
   result = await interrogator.test_chatbot(
       url="https://example.com",
       questions=["Jakie są godziny otwarcia?", "Gdzie się znajdujecie?"]
   )
   print(result.session_log)
   ```

   ### judge-dredd
   ```python
   from src.agents.judge_dredd import JudgeDredd
   
   judge = JudgeDredd()
   verdict = await judge.verify(
       question="Jakie są godziny otwarcia?",
       chatbot_answer="Jesteśmy otwarci od 8 do 16.",
       rag_context=["Godziny otwarcia: 8:00-16:00 w dni robocze"]
   )
   print(f"Ocena: {verdict.category} ({verdict.confidence}%)")
   ```

   ### prompt-refiner
   ```python
   from src.agents.prompt_refiner import PromptRefiner
   
   refiner = PromptRefiner()
   improved = await refiner.improve_prompt(
       original_prompt="Jesteś pomocnym asystentem...",
       errors=["Halucynacja o cenach", "Zły ton formalny"]
   )
   print(improved.new_prompt)
   ```

3. **Uruchom test**
   ```bash
   cd c:\Users\Trzyb\Desktop\truthseeker
   uv run python -c "
   import asyncio
   # wklej kod testowy tutaj
   asyncio.run(test())
   "
   ```

4. **Zweryfikuj wynik**
   - Sprawdź czy agent zwraca oczekiwane dane
   - Sprawdź logi w konsoli
   - Sprawdź czy nie ma błędów/wyjątków

**Guardrails**
- Testuj tylko jednego agenta na raz
- Używaj danych testowych, nie produkcyjnych
- Sprawdzaj logi infrastruktury (Qdrant, Redis)
