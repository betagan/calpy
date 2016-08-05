import unittest

suite = unittest.TestSuite()
for all_test_suite in unittest.defaultTestLoader.discover('tests', pattern='test*.py'):
    for test_suite in all_test_suite:
        suite.addTests(test_suite)

unittest.TextTestRunner(verbosity=2).run(suite)

