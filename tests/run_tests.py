#!/usr/bin/env python3

import unittest
import os
import sys


def run_tests():
    """Run all tests in the tests directory."""
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests')

    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return non-zero exit code if tests failed
    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == '__main__':
    run_tests()