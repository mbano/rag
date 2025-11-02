#!/usr/bin/env python3
"""
Test runner script for the RAG application.
This script provides an easy way to run all tests with proper configuration.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_path=None, verbose=False, coverage=False, parallel=False):
    """
    Run tests with pytest.

    Args:
        test_path: Specific test file or directory to run
        verbose: Enable verbose output
        coverage: Generate coverage report
        parallel: Run tests in parallel
    """
    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test path if specified
    if test_path:
        cmd.append(str(test_path))
    else:
        cmd.append("tests/")

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add coverage
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])

    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])

    # Add other useful options
    cmd.extend(
        [
            "--tb=short",  # Shorter traceback format
            "--disable-warnings",  # Disable warnings for cleaner output
        ]
    )

    print(f"Running command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Please install it with: pip install pytest")
        return 1


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Run RAG application tests")
    parser.add_argument(
        "test_path",
        nargs="?",
        help="Specific test file or directory to run (default: all tests)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-c", "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "-p", "--parallel", action="store_true", help="Run tests in parallel"
    )
    # Marker options removed - tests can be run by file path instead

    args = parser.parse_args()

    # Determine test path
    test_path = args.test_path

    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the project root directory")
        return 1

    # Run tests
    return run_tests(
        test_path=test_path,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
    )


if __name__ == "__main__":
    sys.exit(main())
