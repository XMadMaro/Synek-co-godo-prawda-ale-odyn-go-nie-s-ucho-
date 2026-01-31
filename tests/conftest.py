"""
TruthSeeker - Test Configuration and Fixtures
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.verification import VerificationAgent, TaskResult
from src.infrastructure.llm_client import LLMClient


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary project root for testing."""
    # Create basic project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")

    return tmp_path


@pytest.fixture
def valid_python_file(project_root: Path) -> str:
    """Create a valid Python file for testing."""
    file_path = project_root / "src" / "valid.py"
    file_path.write_text('''
"""Valid Python module."""

from typing import Optional


def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


class Calculator:
    """Simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
''')
    return "src/valid.py"


@pytest.fixture
def invalid_python_file(project_root: Path) -> str:
    """Create an invalid Python file for testing."""
    file_path = project_root / "src" / "invalid.py"
    file_path.write_text('''
def broken_function(
    # Missing closing parenthesis
    print("oops")
''')
    return "src/invalid.py"


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    mock = MagicMock(spec=LLMClient)
    mock.chat_json = AsyncMock(return_value={
        "passed": True,
        "issues": [],
        "summary": "Code looks good"
    })
    return mock


@pytest.fixture
def verification_agent(project_root: Path, mock_llm_client: MagicMock) -> VerificationAgent:
    """Create a VerificationAgent with mocked dependencies."""
    agent = VerificationAgent(project_root=str(project_root))
    agent.llm_client = mock_llm_client
    return agent


@pytest.fixture
def task_result_valid(valid_python_file: str) -> TaskResult:
    """Create a TaskResult for valid file."""
    return TaskResult(
        task_id="test-001",
        files_modified=[valid_python_file],
        success=True,
        output="Task completed",
    )


@pytest.fixture
def task_result_invalid(invalid_python_file: str) -> TaskResult:
    """Create a TaskResult for invalid file."""
    return TaskResult(
        task_id="test-002",
        files_modified=[invalid_python_file],
        success=True,
        output="Task completed",
    )
