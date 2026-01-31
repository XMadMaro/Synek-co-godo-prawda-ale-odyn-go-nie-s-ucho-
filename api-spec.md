# API Specification

## Base URL
```
https://api.chatbot-auditor.local/api/v1
```

## Autentykacja
```
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### 🔍 Auditor

#### POST /audit/session
Rozpoczyna sesję audytu chatbota.

**Request:**
```json
{
  "target_url": "https://example.com/chatbot",
  "questions_count": 20,
  "categories": ["urzędowe", "transport", "odpady"]
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "status": "running",
  "estimated_time": 120
}
```

#### GET /audit/session/{session_id}
Status sesji audytu.

#### GET /audit/report/{session_id}
Pobiera raport z audytu.

**Response:**
```json
{
  "session_id": "uuid",
  "target_url": "https://example.com/chatbot",
  "total_questions": 20,
  "results": {
    "correct": 12,
    "incorrect": 5,
    "partial": 3
  },
  "score": 0.675,
  "details": [
    {
      "question": "Jakie są godziny otwarcia urzędu?",
      "chatbot_answer": "8:00-16:00",
      "rag_answer": "8:00-15:00 (piątek do 14:00)",
      "verdict": "partial",
      "confidence": 0.7
    }
  ]
}
```

---

### 📥 Scraper

#### POST /scrape/url
Scrapuje pojedynczy URL.

**Request:**
```json
{
  "url": "https://urzad.gov.pl/page",
  "depth": 2,
  "include_pdfs": true
}
```

#### POST /scrape/batch
Scrapuje listę URL-i.

**Request:**
```json
{
  "urls": ["url1", "url2"],
  "priority": "high"
}
```

#### GET /scrape/job/{job_id}
Status zadania scrapingu.

---

### 📚 Knowledge Base (RAG)

#### POST /rag/query
Zapytanie do bazy wiedzy.

**Request:**
```json
{
  "query": "Jak złożyć wniosek o dowód?",
  "top_k": 5,
  "min_score": 0.7
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "Aby złożyć wniosek o dowód osobisty...",
      "source": "https://urzad.gov.pl/dowody",
      "score": 0.92,
      "fact_check_status": "verified",
      "last_updated": "2026-01-15"
    }
  ]
}
```

#### GET /rag/documents
Lista dokumentów w bazie.

#### DELETE /rag/document/{doc_id}
Usuwa dokument z bazy.

---

### ✅ Fact-Checker

#### POST /facts/verify
Weryfikuje fakt.

**Request:**
```json
{
  "claim": "Urząd jest czynny w soboty",
  "context": "Godziny otwarcia urzędu miejskiego"
}
```

**Response:**
```json
{
  "claim": "Urząd jest czynny w soboty",
  "verdict": "false",
  "confidence": 0.95,
  "sources": [
    {
      "url": "https://urzad.gov.pl/kontakt",
      "excerpt": "Urząd czynny: pon-pt 8:00-16:00"
    }
  ]
}
```

#### GET /facts/conflicts
Lista wykrytych sprzeczności.

---

## Kody Błędów

| Kod | Opis |
|-----|------|
| 400 | Nieprawidłowe parametry |
| 401 | Brak autoryzacji |
| 404 | Zasób nie znaleziony |
| 429 | Rate limit exceeded |
| 500 | Błąd serwera |

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| /audit/* | 10/min |
| /scrape/* | 20/min |
| /rag/query | 100/min |
| /facts/* | 50/min |
