#!/usr/bin/env python
import unittest
import otrs_search
import os, sys, tempfile

class TestSearch(unittest.TestCase):

    def test_conf(self):
        otrs_search.get_conf()
        self.assertNotEqual(otrs_search.HOST, '')

    def test_login(self):
        sessfile = '%s/%s'%(tempfile.gettempdir(), otrs_search.OTRS_SESSION)
        os.remove(sessfile)
        otrs_search.get_conf()
        otrs_search.create_session()
        self.assertTrue(os.path.exists(sessfile))

    def test_search(self):
        args = ['-a', '1', '-u', 'day', '-g']
        otrs_search.get_args(args)
        res = otrs_search.get_tickets()
        otrs_search.show_tickets(res)
        return True

if __name__ == '__main__':
    unittest.main()
