"""
Test runner script for OpenCode Python tools
"""
import os
import sys
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.tools.test_file_tools import TestFileTools  # noqa: E402
from test.tools.test_math_tools import TestMathTools  # noqa: E402


def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestMathTools))
    test_suite.addTest(unittest.makeSuite(TestFileTools))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
