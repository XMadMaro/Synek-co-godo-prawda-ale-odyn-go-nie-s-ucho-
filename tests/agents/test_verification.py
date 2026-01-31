"""
Tests for VerificationAgent
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.verification import VerificationAgent, TaskResult
from src.core.models import (
    VerificationStatus,
    VerificationRecommendation,
    CheckResult,
)


class TestVerificationAgent:
    """Tests for VerificationAgent class."""

    @pytest.mark.asyncio
    async def test_check_syntax_valid_file(
        self, verification_agent: VerificationAgent, valid_python_file: str
    ):
        """Test syntax check passes for valid Python file."""
        result = await verification_agent._check_syntax([valid_python_file])

        assert result.passed is True
        assert result.name == "syntax"
        assert "valid" in result.details.lower() or "1 files" in result.details

    @pytest.mark.asyncio
    async def test_check_syntax_invalid_file(
        self, verification_agent: VerificationAgent, invalid_python_file: str
    ):
        """Test syntax check fails for invalid Python file."""
        result = await verification_agent._check_syntax([invalid_python_file])

        assert result.passed is False
        assert result.name == "syntax"

    @pytest.mark.asyncio
    async def test_check_syntax_no_files(self, verification_agent: VerificationAgent):
        """Test syntax check with no Python files."""
        result = await verification_agent._check_syntax(["file.txt", "file.md"])

        assert result.passed is True
        assert "No Python files" in result.details

    @pytest.mark.asyncio
    async def test_check_syntax_nonexistent_file(self, verification_agent: VerificationAgent):
        """Test syntax check with nonexistent file."""
        result = await verification_agent._check_syntax(["nonexistent.py"])

        assert result.passed is True  # Skips nonexistent files

    @pytest.mark.asyncio
    async def test_check_lint_valid_file(
        self, verification_agent: VerificationAgent, valid_python_file: str
    ):
        """Test lint check on valid file."""
        result = await verification_agent._check_lint([valid_python_file])

        # Result depends on whether ruff is installed
        assert result.name == "lint"
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_check_security_valid_file(
        self, verification_agent: VerificationAgent, valid_python_file: str
    ):
        """Test security check on valid file."""
        result = await verification_agent._check_security([valid_python_file])

        assert result.name == "security"
        # Passes if bandit not installed or no issues

    @pytest.mark.asyncio
    async def test_check_patterns_with_mock(
        self, verification_agent: VerificationAgent, valid_python_file: str
    ):
        """Test pattern check with mocked LLM."""
        result = await verification_agent._check_patterns([valid_python_file])

        assert result.name == "patterns"
        assert result.passed is True
        assert "good" in result.details.lower() or "skipped" in result.details.lower()

    @pytest.mark.asyncio
    async def test_execute_valid_file(
        self,
        verification_agent: VerificationAgent,
        task_result_valid: TaskResult,
    ):
        """Test full verification on valid file."""
        result = await verification_agent.execute(task_result_valid)

        assert result.task_id == "test-001"
        assert result.status in [VerificationStatus.PASS, VerificationStatus.WARN]
        assert len(result.checks) >= 5
        assert "syntax" in result.checks
        assert result.overall_confidence >= 0.0

    @pytest.mark.asyncio
    async def test_execute_invalid_file(
        self,
        verification_agent: VerificationAgent,
        task_result_invalid: TaskResult,
    ):
        """Test full verification on invalid file."""
        result = await verification_agent.execute(task_result_invalid)

        assert result.task_id == "test-002"
        assert result.status == VerificationStatus.FAIL
        assert result.recommendation == VerificationRecommendation.RETRY
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_verify_quick(
        self, verification_agent: VerificationAgent, valid_python_file: str
    ):
        """Test quick verification method."""
        result = await verification_agent.verify_quick([valid_python_file])

        assert result.name == "quick"
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_parallel_checks_run(
        self, verification_agent: VerificationAgent, task_result_valid: TaskResult
    ):
        """Test that parallel checks actually run."""
        result = await verification_agent.execute(task_result_valid)

        # All 6 checks should be present
        expected_checks = ["syntax", "types", "lint", "security", "tests", "patterns"]
        for check_name in expected_checks:
            assert check_name in result.checks, f"Missing check: {check_name}"

    @pytest.mark.asyncio
    async def test_weighted_confidence(
        self, verification_agent: VerificationAgent, task_result_valid: TaskResult
    ):
        """Test that confidence is calculated with weights."""
        result = await verification_agent.execute(task_result_valid)

        # Confidence should be between 0 and 1
        assert 0.0 <= result.overall_confidence <= 1.0


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_task_result_creation(self):
        """Test TaskResult can be created."""
        result = TaskResult(
            task_id="test-001",
            files_modified=["file.py"],
            success=True,
        )

        assert result.task_id == "test-001"
        assert result.files_modified == ["file.py"]
        assert result.success is True
        assert result.output == ""
        assert result.error is None

    def test_task_result_with_error(self):
        """Test TaskResult with error."""
        result = TaskResult(
            task_id="test-002",
            files_modified=["file.py"],
            success=False,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"


class TestCheckResult:
    """Tests for CheckResult model."""

    def test_check_result_passed(self):
        """Test CheckResult for passed check."""
        result = CheckResult(
            name="syntax",
            passed=True,
            details="All files valid",
            duration_ms=100,
        )

        assert result.passed is True
        assert result.duration_ms == 100

    def test_check_result_failed(self):
        """Test CheckResult for failed check."""
        result = CheckResult(
            name="types",
            passed=False,
            details="3 type errors found",
        )

        assert result.passed is False
        assert result.duration_ms == 0  # Default
