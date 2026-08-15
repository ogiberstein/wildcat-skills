#!/usr/bin/env python3
"""Run the controller suite and print a pass count."""
import os
import sys
import unittest

here = os.path.dirname(os.path.abspath(__file__))
suite = unittest.defaultTestLoader.discover(here, pattern="test_*.py")
runner = unittest.TextTestRunner(verbosity=1)
result = runner.run(suite)
total = result.testsRun
failed = len(result.failures) + len(result.errors)
print(f"{total - failed}/{total} tests passed")
sys.exit(1 if failed else 0)
