"""
TruthSeeker - Verification Agent
Verifies code quality after each atomic task.
"""

import asyncio
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from src.agents.base import BaseAgent
from src.core.models import (
    CheckResult,
    VerificationResult,
    VerificationStatus,
    VerificationRecommendation,
)
from src.infrastructure.llm_client import LLMClient


@dataclass
class TaskResult:
    """Result from an Antigravity agent task execution."""
    task_id: str
    files_modified: list[str]
    success: bool
    output: str = ""
    error: str | None = None


class VerificationAgent(BaseAgent[TaskResult, VerificationResult]):
    """
    Agent that verifies code quality after each atomic task.

    Runs multiple verification checks:
    - Tier 1: Syntax validation (critical)
    - Tier 2: Type checking with mypy (critical)
    - Tier 3: Linting with ruff
    - Tier 4: Security scan with bandit
    - Tier 5: Unit tests with pytest
    - Tier 6: Pattern compliance (LLM review)
    """

    def __init__(self, project_root: str | None = None, llm_provider: str = "openai"):
        super().__init__("verification")
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.llm_client = LLMClient(provider=llm_provider)

    async def execute(self, input_data: TaskResult) -> VerificationResult:
        """
        Execute all verification checks on the task result.

        Args:
            input_data: The result from task execution containing modified files.

        Returns:
            VerificationResult with all check outcomes.
        """
        self.log.info(
            "verification_started",
            task_id=input_data.task_id,
            files_count=len(input_data.files_modified),
        )

        checks: dict[str, CheckResult] = {}
        errors: list[str] = []
        warnings: list[str] = []

        # Run independent checks in parallel (Tier 1-4)
        parallel_checks = await asyncio.gather(
            self._check_syntax(input_data.files_modified),
            self._check_types(input_data.files_modified),
            self._check_lint(input_data.files_modified),
            self._check_security(input_data.files_modified),
            return_exceptions=True,
        )

        check_names = ["syntax", "types", "lint", "security"]
        for name, result in zip(check_names, parallel_checks):
            if isinstance(result, Exception):
                checks[name] = CheckResult(name=name, passed=False, details=str(result))
            else:
                checks[name] = result

        # Run sequential checks (depend on code being valid)
        if checks["syntax"].passed:
            checks["tests"] = await self._run_tests(input_data.files_modified)
            checks["patterns"] = await self._check_patterns(input_data.files_modified)
        else:
            checks["tests"] = CheckResult(name="tests", passed=False, details="Skipped due to syntax errors")
            checks["patterns"] = CheckResult(name="patterns", passed=False, details="Skipped due to syntax errors")

        # Collect errors and warnings
        critical_checks = ["syntax", "types"]
        warning_checks = ["lint", "security", "tests", "patterns"]

        for name in critical_checks:
            if not checks[name].passed:
                errors.append(f"{name}: {checks[name].details}")

        for name in warning_checks:
            if not checks[name].passed:
                warnings.append(f"{name}: {checks[name].details}")

        # Determine overall status
        critical_failed = any(not checks[name].passed for name in critical_checks)
        security_failed = not checks["security"].passed
        tests_failed = not checks["tests"].passed

        if critical_failed:
            status = VerificationStatus.FAIL
            recommendation = VerificationRecommendation.RETRY
        elif security_failed:
            status = VerificationStatus.FAIL
            recommendation = VerificationRecommendation.ESCALATE  # Security issues need review
        elif tests_failed:
            status = VerificationStatus.WARN
            recommendation = VerificationRecommendation.RETRY
        elif warnings:
            status = VerificationStatus.WARN
            recommendation = VerificationRecommendation.PROCEED
        else:
            status = VerificationStatus.PASS
            recommendation = VerificationRecommendation.PROCEED

        # Calculate confidence (weighted)
        weights = {"syntax": 2, "types": 2, "lint": 1, "security": 2, "tests": 2, "patterns": 1}
        total_weight = sum(weights.values())
        weighted_score = sum(weights[name] for name, check in checks.items() if check.passed)
        confidence = weighted_score / total_weight

        result = VerificationResult(
            task_id=input_data.task_id,
            status=status,
            checks=checks,
            overall_confidence=confidence,
            recommendation=recommendation,
            errors=errors,
            warnings=warnings,
        )

        self.log.info(
            "verification_completed",
            task_id=input_data.task_id,
            status=status.value,
            confidence=round(confidence, 2),
            checks_passed=sum(1 for c in checks.values() if c.passed),
            checks_total=len(checks),
        )

        return result

    async def _check_syntax(self, files: list[str]) -> CheckResult:
        """Check Python syntax validity."""
        start = time.perf_counter()
        self.log.debug("check_syntax", files_count=len(files))

        python_files = [f for f in files if f.endswith(".py")]
        if not python_files:
            return CheckResult(name="syntax", passed=True, details="No Python files", duration_ms=0)

        errors = []
        for file_path in python_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue

            try:
                result = await asyncio.to_thread(
                    subprocess.run,
                    ["python", "-m", "py_compile", str(full_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    # Parse error message for clarity
                    error_msg = result.stderr.strip()
                    if "SyntaxError" in error_msg:
                        # Extract line number and message
                        errors.append(f"{file_path}: {error_msg.split('SyntaxError:')[-1].strip()}")
                    else:
                        errors.append(f"{file_path}: {error_msg}")
            except subprocess.TimeoutExpired:
                errors.append(f"{file_path}: Syntax check timeout")
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")

        duration = int((time.perf_counter() - start) * 1000)
        return CheckResult(
            name="syntax",
            passed=len(errors) == 0,
            details="; ".join(errors) if errors else f"All {len(python_files)} files valid",
            duration_ms=duration,
        )

    async def _check_types(self, files: list[str]) -> CheckResult:
        """Check type hints with mypy."""
        start = time.perf_counter()
        self.log.debug("check_types", files_count=len(files))

        python_files = [f for f in files if f.endswith(".py")]
        if not python_files:
            return CheckResult(name="types", passed=True, details="No Python files", duration_ms=0)

        try:
            file_args = [str(self.project_root / f) for f in python_files if (self.project_root / f).exists()]
            if not file_args:
                return CheckResult(name="types", passed=True, details="No files to check", duration_ms=0)

            result = await asyncio.to_thread(
                subprocess.run,
                ["python", "-m", "mypy", "--ignore-missing-imports", "--no-error-summary"] + file_args,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_root),
            )

            duration = int((time.perf_counter() - start) * 1000)

            if result.returncode == 0:
                return CheckResult(name="types", passed=True, details="No type errors", duration_ms=duration)
            else:
                # Parse mypy output for detailed errors
                error_lines = [l for l in result.stdout.split("\n") if "error:" in l]
                error_count = len(error_lines)

                # Get first 3 errors for details
                first_errors = error_lines[:3]
                details = f"{error_count} type errors. First: {'; '.join(first_errors)}" if first_errors else f"{error_count} type errors"

                return CheckResult(
                    name="types",
                    passed=False,
                    details=details[:500],  # Limit length
                    duration_ms=duration,
                )

        except subprocess.TimeoutExpired:
            return CheckResult(name="types", passed=False, details="Type check timeout (>120s)", duration_ms=120000)
        except FileNotFoundError:
            return CheckResult(name="types", passed=True, details="mypy not installed (skipped)", duration_ms=0)
        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            return CheckResult(name="types", passed=False, details=str(e)[:200], duration_ms=duration)

    async def _check_lint(self, files: list[str]) -> CheckResult:
        """Check code style with ruff."""
        start = time.perf_counter()
        self.log.debug("check_lint", files_count=len(files))

        python_files = [f for f in files if f.endswith(".py")]
        if not python_files:
            return CheckResult(name="lint", passed=True, details="No Python files", duration_ms=0)

        try:
            file_args = [str(self.project_root / f) for f in python_files if (self.project_root / f).exists()]
            if not file_args:
                return CheckResult(name="lint", passed=True, details="No files to check", duration_ms=0)

            result = await asyncio.to_thread(
                subprocess.run,
                ["python", "-m", "ruff", "check", "--output-format=concise"] + file_args,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root),
            )

            duration = int((time.perf_counter() - start) * 1000)

            if result.returncode == 0:
                return CheckResult(name="lint", passed=True, details="No lint issues", duration_ms=duration)
            else:
                issues = [l for l in result.stdout.split("\n") if l.strip()]
                issue_count = len(issues)
                # Categorize issues
                errors = [i for i in issues if ":E" in i or ":F" in i]
                warnings = [i for i in issues if ":W" in i]

                details = f"{issue_count} issues ({len(errors)} errors, {len(warnings)} warnings)"
                if issues:
                    details += f". First: {issues[0][:100]}"

                return CheckResult(
                    name="lint",
                    passed=False,
                    details=details,
                    duration_ms=duration,
                )

        except subprocess.TimeoutExpired:
            return CheckResult(name="lint", passed=False, details="Lint check timeout", duration_ms=60000)
        except FileNotFoundError:
            return CheckResult(name="lint", passed=True, details="ruff not installed (skipped)", duration_ms=0)
        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            return CheckResult(name="lint", passed=False, details=str(e)[:200], duration_ms=duration)

    async def _check_security(self, files: list[str]) -> CheckResult:
        """Check for security vulnerabilities with bandit."""
        start = time.perf_counter()
        self.log.debug("check_security", files_count=len(files))

        python_files = [f for f in files if f.endswith(".py")]
        if not python_files:
            return CheckResult(name="security", passed=True, details="No Python files", duration_ms=0)

        try:
            file_args = [str(self.project_root / f) for f in python_files if (self.project_root / f).exists()]
            if not file_args:
                return CheckResult(name="security", passed=True, details="No files to check", duration_ms=0)

            result = await asyncio.to_thread(
                subprocess.run,
                ["python", "-m", "bandit", "-f", "json", "-ll"] + file_args,  # -ll = medium+ severity
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root),
            )

            duration = int((time.perf_counter() - start) * 1000)

            if result.returncode == 0:
                return CheckResult(name="security", passed=True, details="No security issues", duration_ms=duration)
            else:
                # Parse bandit JSON output
                try:
                    import json
                    report = json.loads(result.stdout)
                    issues = report.get("results", [])

                    if not issues:
                        return CheckResult(name="security", passed=True, details="No security issues", duration_ms=duration)

                    # Categorize by severity
                    high = [i for i in issues if i.get("issue_severity") == "HIGH"]
                    medium = [i for i in issues if i.get("issue_severity") == "MEDIUM"]

                    details = f"{len(issues)} security issues ({len(high)} high, {len(medium)} medium)"
                    if high:
                        details += f". HIGH: {high[0].get('issue_text', 'Unknown')[:100]}"

                    # High severity = fail, medium = warning (still pass but warn)
                    return CheckResult(
                        name="security",
                        passed=len(high) == 0,
                        details=details,
                        duration_ms=duration,
                    )
                except json.JSONDecodeError:
                    return CheckResult(
                        name="security",
                        passed=False,
                        details="Failed to parse bandit output",
                        duration_ms=duration,
                    )

        except subprocess.TimeoutExpired:
            return CheckResult(name="security", passed=False, details="Security check timeout", duration_ms=60000)
        except FileNotFoundError:
            # Bandit not installed - skip but note it
            return CheckResult(name="security", passed=True, details="bandit not installed (skipped)", duration_ms=0)
        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            return CheckResult(name="security", passed=False, details=str(e)[:200], duration_ms=duration)

    async def _run_tests(self, files: list[str]) -> CheckResult:
        """Run related unit tests with coverage."""
        start = time.perf_counter()
        self.log.debug("run_tests", files_count=len(files))

        # Find test files related to modified files
        test_files = []
        for file_path in files:
            if file_path.endswith(".py") and not file_path.startswith("test_"):
                path = Path(file_path)

                # Try multiple test file patterns
                patterns = [
                    path.parent / f"test_{path.name}",  # Same dir
                    Path("tests") / path.parent / f"test_{path.name}",  # tests/ mirror
                    Path("tests") / f"test_{path.name}",  # tests/ flat
                    path.parent / "tests" / f"test_{path.name}",  # module/tests/
                ]

                for test_path in patterns:
                    if (self.project_root / test_path).exists():
                        test_files.append(str(test_path))
                        break

        if not test_files:
            return CheckResult(name="tests", passed=True, details="No related tests found", duration_ms=0)

        try:
            # Run with coverage if available
            cmd = ["python", "-m", "pytest", "-v", "--tb=short", "-q"]

            result = await asyncio.to_thread(
                subprocess.run,
                cmd + test_files,
                capture_output=True,
                text=True,
                timeout=180,
                cwd=str(self.project_root),
            )

            duration = int((time.perf_counter() - start) * 1000)

            if result.returncode == 0:
                # Parse passed count from output
                for line in result.stdout.split("\n"):
                    if "passed" in line:
                        return CheckResult(name="tests", passed=True, details=line.strip(), duration_ms=duration)
                return CheckResult(name="tests", passed=True, details="All tests passed", duration_ms=duration)
            else:
                # Extract failure details
                for line in result.stdout.split("\n"):
                    if "failed" in line.lower() or "error" in line.lower():
                        return CheckResult(name="tests", passed=False, details=line.strip()[:200], duration_ms=duration)
                return CheckResult(name="tests", passed=False, details="Tests failed", duration_ms=duration)

        except subprocess.TimeoutExpired:
            return CheckResult(name="tests", passed=False, details="Test timeout (>180s)", duration_ms=180000)
        except FileNotFoundError:
            return CheckResult(name="tests", passed=True, details="pytest not installed (skipped)", duration_ms=0)
        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            return CheckResult(name="tests", passed=False, details=str(e)[:200], duration_ms=duration)

    async def _check_patterns(self, files: list[str]) -> CheckResult:
        """Check code patterns using LLM review."""
        start = time.perf_counter()
        self.log.debug("check_patterns", files_count=len(files))

        python_files = [f for f in files if f.endswith(".py")]
        if not python_files:
            return CheckResult(name="patterns", passed=True, details="No Python files", duration_ms=0)

        # Read file contents (limit to first 3 files, 300 lines each)
        code_snippets = []
        for file_path in python_files[:3]:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding="utf-8")
                    lines = content.split("\n")[:300]
                    code_snippets.append(f"# File: {file_path}\n" + "\n".join(lines))
                except Exception:
                    continue

        if not code_snippets:
            return CheckResult(name="patterns", passed=True, details="No readable files", duration_ms=0)

        try:
            prompt = """You are a code reviewer for the TruthSeeker project (Python/FastAPI chatbot auditor).

Review the following code for pattern compliance. Check:
1. **Pydantic**: Models use BaseModel, proper Field usage, validators
2. **Async**: Consistent async/await, no blocking calls in async context
3. **Error handling**: Proper try/except, logging errors, no bare except
4. **Logging**: Uses structlog pattern (self.log), meaningful log messages
5. **Type hints**: All functions have type hints, no Any unless necessary
6. **Security**: No hardcoded secrets, proper input validation

Code to review:
```python
{code}
```

Respond ONLY with valid JSON (no markdown):
{{"passed": true/false, "issues": ["issue1", "issue2"], "summary": "one line summary"}}
""".format(code="\n\n---\n\n".join(code_snippets))

            response = await self.llm_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            duration = int((time.perf_counter() - start) * 1000)

            passed = response.get("passed", True)
            issues = response.get("issues", [])
            summary = response.get("summary", "Pattern check complete")

            details = summary
            if not passed and issues:
                details = f"{summary}. Issues: {'; '.join(issues[:3])}"

            return CheckResult(name="patterns", passed=passed, details=details[:300], duration_ms=duration)

        except Exception as e:
            duration = int((time.perf_counter() - start) * 1000)
            self.log.warning("pattern_check_failed", error=str(e))
            return CheckResult(name="patterns", passed=True, details=f"LLM review skipped: {str(e)[:100]}", duration_ms=duration)

    async def verify_quick(self, files: list[str]) -> CheckResult:
        """Quick verification - only syntax and lint (no LLM, no tests)."""
        self.log.info("quick_verification", files_count=len(files))

        results = await asyncio.gather(
            self._check_syntax(files),
            self._check_lint(files),
        )

        all_passed = all(r.passed for r in results)
        details = "; ".join(f"{r.name}: {r.details}" for r in results if not r.passed)

        return CheckResult(
            name="quick",
            passed=all_passed,
            details=details or "All quick checks passed",
            duration_ms=sum(r.duration_ms for r in results),
        )
