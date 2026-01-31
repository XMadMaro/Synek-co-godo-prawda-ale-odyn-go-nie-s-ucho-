# ChatBot Auditor & RAG Knowledge Base

## Opis Projektu
Aplikacja do audytu chatbotów na stronach internetowych oraz budowania wiarygodnej bazy wiedzy RAG dla asystenta mieszkańca.

## Główne Funkcjonalności

### 1. ChatBot Auditor
- Automatyczne przepytywanie chatbotów na stronach
- Weryfikacja odpowiedzi z własną bazą wiedzy
- Raportowanie błędów i nieścisłości

### 2. Inteligentny Scraper
- Ekstrakcja danych ze stron urzędowych/miejskich
- Parsowanie dokumentów PDF, HTML
- Strukturyzacja danych do formatu RAG

### 3. Fact-Checker
- Weryfikacja faktów z wielu źródeł
- Scoring wiarygodności danych
- Flagowanie sprzecznych informacji

### 4. Baza Wiedzy RAG
- Wektorowa baza danych (embeddings)
- Wersjonowanie i aktualizacje
- API do zapytań semantycznych

## Stack Technologiczny (Antigravity)
- **Backend**: Python/FastAPI
- **Baza wektorowa**: Qdrant/Pinecone
- **LLM**: OpenAI/Anthropic API
- **Scraping**: Playwright, BeautifulSoup
- **Frontend**: React/Next.js

## Instalacja w Antigravity
```bash
# Klonowanie repozytorium
git clone [repo-url]
cd chatbot-auditor

# Instalacja zależności
uv sync

# Konfiguracja środowiska
cp .env.example .env
# Uzupełnij klucze API w .env

# Uruchomienie
uv run python main.py
```

## Struktura Projektu
```
/src
  /auditor      - Moduł przepytywania chatbotów
  /scraper      - Inteligentny scraper
  /fact_checker - Weryfikacja faktów
  /rag          - Baza wiedzy RAG
  /api          - Endpointy REST
/tests
/docs
```
