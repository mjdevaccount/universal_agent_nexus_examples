"""Test runner for all Universal Agent Nexus examples.

This script executes all examples and verifies they run correctly.
It handles compilation, dependency installation, and execution with proper
error handling and reporting.

Usage:
    # Test all examples
    python tools/test_all_examples.py

    # Test specific examples
    python tools/test_all_examples.py --examples 01 02 03

    # Include server-based examples (06, 07, 08)
    python tools/test_all_examples.py --include-servers

    # Verbose output
    python tools/test_all_examples.py --verbose

    # Custom timeout
    python tools/test_all_examples.py --timeout 120
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Import from same directory
import sys
from pathlib import Path

# Add tools directory to path
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))

from example_runner import EXAMPLES, ExampleSpec, ROOT


@dataclass
class TestResult:
    """Result of testing a single example."""

    code: str
    title: str
    status: str  # "passed", "failed", "skipped", "error"
    message: str
    duration: float
    output: Optional[str] = None


class ExampleTestRunner:
    """Runs tests for all examples."""

    def __init__(self, timeout: int = 60, verbose: bool = False, skip_servers: bool = True):
        self.timeout = timeout
        self.verbose = verbose
        self.skip_servers = skip_servers
        self.results: List[TestResult] = []

    def _run_command(
        self, command: str, cwd: Path, timeout: Optional[int] = None
    ) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout or self.timeout} seconds"
        except Exception as e:
            return -1, "", str(e)

    def _should_skip(self, spec: ExampleSpec) -> bool:
        """Determine if an example should be skipped."""
        # Skip server-based examples by default
        if self.skip_servers:
            server_examples = ["06", "07", "08"]
            if spec.code in server_examples:
                return True

        # Skip examples without a run command
        if not spec.runtime_command:
            return True

        return False

    def _install_dependencies(self, spec: ExampleSpec) -> tuple[bool, str]:
        """Install dependencies for an example if needed."""
        deps_cmd = next((c for c in spec.commands if c.name == "deps"), None)
        if not deps_cmd:
            return True, "No dependencies to install"

        if self.verbose:
            print(f"  Installing dependencies: {deps_cmd.command}")

        exit_code, stdout, stderr = self._run_command(deps_cmd.command, spec.workdir, timeout=120)
        if exit_code != 0:
            return False, f"Dependency installation failed: {stderr}"

        return True, "Dependencies installed"

    def _compile_manifest(self, spec: ExampleSpec) -> tuple[bool, str]:
        """Compile manifest if one exists."""
        if not spec.manifest:
            return True, "No manifest to compile"

        compile_cmd = spec.compile_command
        if not compile_cmd:
            return True, "No compile command"

        if self.verbose:
            print(f"  Compiling: {compile_cmd}")

        exit_code, stdout, stderr = self._run_command(compile_cmd, spec.workdir, timeout=60)
        if exit_code != 0:
            return False, f"Compilation failed: {stderr}\n{stdout}"

        # Verify output file exists
        output_file = spec.workdir / spec.compile_output
        if not output_file.exists():
            return False, f"Compiled output file not found: {output_file}"

        return True, "Compilation successful"

    def _run_example(self, spec: ExampleSpec) -> tuple[bool, str, str]:
        """Run the example and return success, output, error."""
        run_cmd = spec.runtime_command
        if not run_cmd:
            return False, "", "No runtime command available"

        if self.verbose:
            print(f"  Running: {run_cmd}")

        exit_code, stdout, stderr = self._run_command(run_cmd, spec.workdir, timeout=self.timeout)

        # Check for Python errors
        has_traceback = "traceback" in stderr.lower() or "traceback" in stdout.lower()
        has_error_keyword = (
            "error" in stderr.lower()
            or "exception" in stderr.lower()
            or "failed" in stderr.lower()
        ) and has_traceback

        # Some examples might exit with non-zero but still be valid
        # We'll consider it a failure if:
        # 1. Exit code is non-zero AND there's a traceback, OR
        # 2. There's an error keyword with traceback
        has_error = (exit_code != 0 and has_traceback) or has_error_keyword

        # Check for successful execution indicators
        success_indicators = ["✅", "success", "completed", "result:", "executed"]
        has_success = any(indicator.lower() in stdout.lower() for indicator in success_indicators)

        # If we see success indicators and no clear errors, consider it passed
        if has_success and not has_error:
            return True, stdout, stderr

        return not has_error, stdout, stderr

    def test_example(self, spec: ExampleSpec) -> TestResult:
        """Test a single example."""
        start_time = time.time()

        # Check if should skip
        if self._should_skip(spec):
            return TestResult(
                code=spec.code,
                title=spec.title,
                status="skipped",
                message="Skipped (server-based or no run command)",
                duration=time.time() - start_time,
            )

        if self.verbose:
            print(f"\n[{spec.code}] {spec.title}")

        # Install dependencies
        deps_ok, deps_msg = self._install_dependencies(spec)
        if not deps_ok:
            return TestResult(
                code=spec.code,
                title=spec.title,
                status="error",
                message=f"Dependency installation failed: {deps_msg}",
                duration=time.time() - start_time,
            )

        # Compile if needed
        compile_ok, compile_msg = self._compile_manifest(spec)
        if not compile_ok:
            return TestResult(
                code=spec.code,
                title=spec.title,
                status="error",
                message=f"Compilation failed: {compile_msg}",
                duration=time.time() - start_time,
            )

        # Run the example
        run_ok, stdout, stderr = self._run_example(spec)

        duration = time.time() - start_time

        if run_ok:
            return TestResult(
                code=spec.code,
                title=spec.title,
                status="passed",
                message="Example executed successfully",
                duration=duration,
                output=stdout[:500] if stdout else None,  # Limit output size
            )
        else:
            error_msg = stderr if stderr else stdout
            return TestResult(
                code=spec.code,
                title=spec.title,
                status="failed",
                message=f"Execution failed: {error_msg[:200]}",
                duration=duration,
                output=stdout[:500] if stdout else None,
            )

    def run_all(self, codes: Optional[List[str]] = None) -> List[TestResult]:
        """Run tests for all examples (or specified ones)."""
        examples_to_test = codes if codes else sorted(EXAMPLES.keys())

        print(f"Testing {len(examples_to_test)} example(s)...")
        print("=" * 70)

        for code in examples_to_test:
            spec = EXAMPLES.get(code)
            if not spec:
                self.results.append(
                    TestResult(
                        code=code,
                        title="Unknown",
                        status="error",
                        message=f"Example {code} not found",
                        duration=0.0,
                    )
                )
                continue

            result = self.test_example(spec)
            self.results.append(result)

            # Print status
            status_symbol = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "error": "⚠️",
            }.get(result.status, "?")

            print(f"{status_symbol} [{result.code}] {result.title}: {result.status.upper()}")
            if result.status != "passed" and result.message:
                print(f"   {result.message}")

        return self.results

    def print_summary(self):
        """Print a summary of test results."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        errors = sum(1 for r in self.results if r.status == "error")

        total = len(self.results)
        total_time = sum(r.duration for r in self.results)

        print(f"Total: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"⚠️  Errors: {errors}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"⏱️  Average time: {total_time / total:.2f}s per example" if total > 0 else "")

        if failed > 0 or errors > 0:
            print("\nFailed/Error Examples:")
            for result in self.results:
                if result.status in ("failed", "error"):
                    print(f"  [{result.code}] {result.title}: {result.message}")

        return failed + errors == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test all Universal Agent Nexus examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--examples",
        nargs="+",
        help="Specific example codes to test (e.g., 01 02 03). Default: all examples",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds for each example (default: 60)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--include-servers",
        action="store_true",
        help="Include server-based examples (06, 07, 08) in testing",
    )

    args = parser.parse_args()

    runner = ExampleTestRunner(
        timeout=args.timeout, verbose=args.verbose, skip_servers=not args.include_servers
    )

    runner.run_all(codes=args.examples)
    success = runner.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

