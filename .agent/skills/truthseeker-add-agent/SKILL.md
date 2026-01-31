---
name: truthseeker-add-agent
description: Dodaj nowego agenta do systemu TruthSeeker - szablon i integracja z orchestratorem
license: MIT
compatibility: Python 3.11+
metadata:
  author: user
  version: "1.0"
  language: pl
  project: truthseeker
---

Dodaj nowego agenta do systemu TruthSeeker.

**Input**: Nazwa agenta i jego odpowiedzialność

**Steps**

1. **Określ rolę agenta**

   Zdefiniuj:
   - Nazwa (kebab-case): np. `fact-checker`
   - Klasa Python (PascalCase): np. `FactChecker`
   - Odpowiedzialność: Co robi agent?
   - Dane wejściowe: Co otrzymuje?
   - Dane wyjściowe: Co zwraca?

2. **Utwórz plik agenta**

   ```bash
   cd c:\Users\Trzyb\Desktop\truthseeker\src\agents
   ```

   Utwórz `<agent_name>.py` z szablonem:

   ```python
   """
   <AgentName> Agent
   
   Odpowiedzialność: <opis>
   """
   
   import logging
   from dataclasses import dataclass
   from typing import Optional
   
   from src.core.config import settings
   from src.infrastructure.llm_client import LLMClient
   
   logger = logging.getLogger(__name__)
   
   
   @dataclass
   class <AgentName>Input:
       """Dane wejściowe dla agenta."""
       # Zdefiniuj pola wejściowe
       pass
   
   
   @dataclass
   class <AgentName>Output:
       """Wynik pracy agenta."""
       success: bool
       # Zdefiniuj pola wyjściowe
       error: Optional[str] = None
   
   
   class <AgentName>:
       """
       Agent <nazwa> w systemie TruthSeeker.
       
       <Szczegółowy opis roli i odpowiedzialności>
       """
       
       def __init__(self):
           self.llm = LLMClient()
           logger.info(f"Zainicjalizowano agenta <AgentName>")
       
       async def process(self, input_data: <AgentName>Input) -> <AgentName>Output:
           """
           Główna metoda przetwarzania.
           
           Args:
               input_data: Dane wejściowe
               
           Returns:
               <AgentName>Output z wynikiem
           """
           try:
               logger.info(f"Rozpoczynam przetwarzanie: {input_data}")
               
               # TODO: Implementacja logiki agenta
               
               return <AgentName>Output(success=True)
               
           except Exception as e:
               logger.error(f"Błąd agenta: {e}")
               return <AgentName>Output(success=False, error=str(e))
   ```

3. **Dodaj System Prompt**

   Dodaj prompt do `truthseeker_prompts.md`:

   ```markdown
   ## X. Prompt Systemowy dla Agenta <AgentName>
   
   ### Definicja Roli
   <Opisz rolę agenta>
   
   ### Zasady Działania
   <Opisz jak agent ma działać>
   
   ### Oczekiwany Wynik
   <Opisz co agent ma zwracać>
   ```

4. **Zarejestruj w Orchestratorze**

   Edytuj `src/agents/orchestrator.py`:

   ```python
   from src.agents.<agent_name> import <AgentName>
   
   class Orchestrator:
       def __init__(self):
           # ... istniejący kod ...
           self.<agent_name> = <AgentName>()
   ```

5. **Dodaj testy**

   Utwórz `tests/test_<agent_name>.py`:

   ```python
   import pytest
   from src.agents.<agent_name> import <AgentName>, <AgentName>Input
   
   @pytest.mark.asyncio
   async def test_<agent_name>_basic():
       agent = <AgentName>()
       result = await agent.process(<AgentName>Input(...))
       assert result.success
   ```

6. **Zaktualizuj dokumentację**

   Edytuj `agents.md` - dodaj nowego agenta do listy.
   Edytuj `architecture.md` - dodaj do diagramu.

**Guardrails**
- Każdy agent ma jedną odpowiedzialność (SRP)
- Agent musi mieć Input i Output dataclass
- Agent musi logować swoje działania
- Agent musi obsługiwać błędy gracefully
- Agent musi mieć System Prompt w dokumentacji
