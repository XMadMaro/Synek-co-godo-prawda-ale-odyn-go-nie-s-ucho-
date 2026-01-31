---
name: truthseeker-improve-prompt
description: Ulepsz System Prompt chatbota na podstawie raportu błędów - wykorzystaj agenta Prompt-Refiner
license: MIT
compatibility: Wymaga raportu z Judge-Dredd
metadata:
  author: user
  version: "1.0"
  language: pl
  project: truthseeker
---

Ulepsz System Prompt chatbota na podstawie raportu weryfikacyjnego.

**Input**: 
- Raport błędów od Judge-Dredd
- Oryginalny System Prompt chatbota (opcjonalnie)

**Steps**

1. **Przeanalizuj raport błędów**

   Zidentyfikuj typy błędów:
   | Typ błędu | Przyczyna w prompcie | Rozwiązanie |
   |-----------|---------------------|-------------|
   | Halucynacja | Brak instrukcji "nie wiem" | Dodaj guardrails |
   | Błąd merytoryczny | Za mało kontekstu RAG | Wzmocnij grounding |
   | Zły ton | Nieodpowiednia persona | Popraw ton/styl |
   | Ignorowanie reguł | Słabe constraints | Wzmocnij ograniczenia |

2. **Wyekstrahuj wzorce błędów**

   ```python
   # Przykład analizy
   errors = [
       {"type": "halucynacja", "details": "Zmyślone godziny otwarcia"},
       {"type": "błąd", "details": "Nieprawidłowa cena usługi"},
   ]
   
   patterns = {
       "halucynacja": 2,
       "błąd_merytoryczny": 3,
       "zły_ton": 0
   }
   ```

3. **Zastosuj techniki naprawcze**

   ### Few-Shot Prompting
   Dodaj przykłady poprawnego zachowania:
   ```
   Przykłady odpowiedzi:
   
   User: Ile kosztuje wydanie paszportu?
   Assistant: Opłata za wydanie paszportu wynosi 140 zł dla osoby 
   dorosłej. Źródło: cennik usług paszportowych.
   
   User: Kiedy jest otwarty urząd?
   Assistant: Przepraszam, nie mam informacji o godzinach otwarcia 
   tego konkretnego urzędu. Proszę sprawdzić na stronie urzędu.
   ```

   ### Negative Constraints
   Dodaj wyraźne zakazy:
   ```
   ZAKAZY:
   - NIE wymyślaj informacji, których nie ma w kontekście
   - NIE podawaj kwot/cen bez źródła
   - NIE obiecuj terminów realizacji
   - NIE dawaj porad prawnych ani finansowych
   ```

   ### Context Grounding
   Wzmocnij opieranie się na RAG:
   ```
   Odpowiadaj WYŁĄCZNIE na podstawie dostarczonego kontekstu.
   Jeśli kontekst nie zawiera odpowiedzi, powiedz szczerze:
   "Nie posiadam tej informacji w mojej bazie wiedzy."
   ```

   ### Chain of Thought
   Dla złożonych pytań:
   ```
   Przed odpowiedzią przemyśl krok po kroku:
   1. Czy pytanie dotyczy informacji w mojej bazie?
   2. Jakie fragmenty kontekstu są relevantne?
   3. Czy mogę udzielić pełnej odpowiedzi?
   4. Czy muszę czegoś dopytać?
   ```

4. **Wygeneruj ulepszony prompt**

   Struktura ulepszonego promptu:
   ```markdown
   # System Prompt v2.0
   
   ## Rola
   [Zaktualizowany opis roli]
   
   ## Tone of Voice
   [Poprawiony ton komunikacji]
   
   ## Guardrails
   [Nowe ograniczenia zapobiegające błędom]
   
   ## Przykłady
   [Few-shot examples]
   
   ## Zakazy
   [Negative constraints]
   
   ## Format Odpowiedzi
   [Struktura odpowiedzi]
   ```

5. **Porównaj wersje**

   ```diff
   - Jesteś pomocnym asystentem.
   + Jesteś pomocnym asystentem miejskim, który odpowiada 
   + WYŁĄCZNIE na podstawie dostarczonego kontekstu.
   
   + ## Guardrails
   + - Jeśli nie znasz odpowiedzi, powiedz "Nie wiem"
   + - Zawsze podawaj źródło informacji
   + - Nie wymyślaj danych liczbowych
   ```

6. **Zapisz wynik**

   Zapisz do:
   - `truthseeker/prompts/improved/<chatbot-name>-v2.md`
   
   Dołącz:
   - Analizę przyczyn błędów
   - Uzasadnienie zmian
   - Instrukcję wdrożenia

**Output**
Zwróć:
1. Analiza przyczyn błędów
2. Ulepszony System Prompt (gotowy do użycia)
3. Uzasadnienie kluczowych zmian
4. Sugerowane metryki do monitorowania
