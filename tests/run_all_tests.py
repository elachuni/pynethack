#!/usr/bin/python

import unittest

def main():
    suite = unittest.TestSuite()

    for moduleName in ['test_items', 'test_nethackplayer', 'test_connection',
                       'test_scraper', 'test_endings']:
        module = __import__(moduleName)
        suite.addTest (module.suite())

    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    main()
