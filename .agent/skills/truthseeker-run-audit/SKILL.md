---
name: truthseeker-run-audit
description: Uruchom pełny audyt chatbota - od scrapowania przez indeksowanie do generowania raportu weryfikacyjnego
license: MIT
compatibility: Wymaga uruchomionej infrastruktury (docker-compose up) i skonfigurowanego .env
metadata:
  author: user
  version: "1.0"
  language: pl
  project: truthseeker
---

Uruchom pełny pipeline audytu chatbota TruthSeeker.

**Input**: URL strony z chatbotem do audytu (np. https://um.katowice.pl)

**Pre-requisites**
Przed uruchomieniem upewnij się:
- [ ] Docker działa (`docker ps`)
- [ ] Infrastruktura uruchomiona (`docker-compose up -d` w katalogu truthseeker)
- [ ] `.env` skonfigurowany z OPENAI_API_KEY
- [ ] Zależności zainstalowane (`uv sync`)
- [ ] Playwright zainstalowany (`uv run playwright install`)

**Steps**

1. **Sprawdź infrastrukturę**
   ```bash
   cd c:\Users\Trzyb\Desktop\truthseeker
   docker-compose ps
   ```
   Zweryfikuj że Qdrant, PostgreSQL i Redis działają.

2. **Uruchom API TruthSeeker**
   ```bash
   uv run python -m src.api.main
   ```
   API powinno być dostępne na http://localhost:8000

3. **Sprawdź health endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Uruchom audyt**
   ```bash
   curl -X POST http://localhost:8000/api/v1/audit \
     -H "Content-Type: application/json" \
     -d '{"url": "<URL_CHATBOTA>"}'
   ```
   
   Pipeline wykonuje:
   - **Faza 1**: Scraper-Intel pobiera treść strony
   - **Faza 2**: Knowledge-Architect indeksuje do Qdrant
   - **Faza 3**: Chat-Interrogator testuje chatbota
   - **Faza 4**: Judge-Dredd weryfikuje odpowiedzi
   - **Faza 5**: Prompt-Refiner generuje ulepszenia

5. **Odbierz raport**
   Raport zawiera:
   - Ocenę ogólną chatbota
   - Listę pytań i odpowiedzi
   - Weryfikację każdej odpowiedzi
   - Rekomendacje ulepszeń System Promptu

**Troubleshooting**

| Problem | Rozwiązanie |
|---------|-------------|
| Qdrant niedostępny | `docker-compose up -d qdrant` |
| Brak OPENAI_API_KEY | Uzupełnij w `.env` |
| Playwright error | `uv run playwright install` |
| Port zajęty | Sprawdź `netstat -ano | findstr :8000` |

**Output**
Zapisz raport do `truthseeker/reports/<timestamp>-<domain>.json`
