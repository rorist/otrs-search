#!/usr/bin/env python
import unittest
import otrs_search
import os, sys, re, tempfile

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
        out = sys.stdout.getvalue()
        a = 'ticket(s)' in out
        b = 'CSV:' in out
        self.assertTrue(a and b)

    def test_queues(self):
        args = ['-Q']
        try:
            otrs_search.get_args(args)
        except SystemExit, e:
            out = sys.stdout.getvalue()
            self.assertIsNotNone(re.search('\d+ -*', out))
            self.assertEquals(e.code, 0)
        else:
            self.fail('SystemExit expected')

if __name__ == '__main__':
    unittest.main(buffer=True)
