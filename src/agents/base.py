"""
TruthSeeker - Base Agent Interface
Abstract base class for all agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from src.core.logging import get_logger

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all TruthSeeker agents.

    Each agent should:
    1. Define input/output types
    2. Implement the `execute` method
    3. Handle errors gracefully
    """

    def __init__(self, name: str):
        self.name = name
        self.log = get_logger(f"agent.{name}")

    @abstractmethod
    async def execute(self, input_data: InputT) -> OutputT:
        """
        Execute the agent's main task.

        Args:
            input_data: The input data for the agent.

        Returns:
            The output data from the agent.
        """
        pass

    async def run(self, input_data: InputT) -> OutputT:
        """
        Run the agent with logging and error handling.

        This is the public entry point for agent execution.
        """
        self.log.info("agent_started", input_type=type(input_data).__name__)

        try:
            result = await self.execute(input_data)
            self.log.info(
                "agent_completed",
                output_type=type(result).__name__,
            )
            return result
        except Exception as e:
            self.log.error(
                "agent_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for this agent.
        Override in subclasses for agent-specific prompts.
        """
        return ""
