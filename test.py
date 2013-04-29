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

    def test_queue_id(self):
        args = ['-q', '1', '-u', 'year', '-a', '1', '-g']
        self.search(args)

    def test_queue_name(self):
        args = ['-q', 'a', '-u', 'year', '-a', '1', '-g']
        self.search(args)

    def test_search_basic(self):
        args = ['-a', '1', '-u', 'year', '-g']
        self.search(args)

    def search(self, args):
        otrs_search.get_args(args)
        res = otrs_search.get_tickets()
        csvfile = otrs_search.write_data(res)
        try:
            otrs_search.show_tickets(csvfile)
        except SystemExit, e:
            out = sys.stdout.getvalue()
            a = 'ticket(s)' in out
            self.assertTrue(a)
            self.assertEquals(e.code, 0)
        else:
            out = sys.stdout.getvalue()
            a = 'ticket(s)' in out
            b = 'CSV:' in out
            self.assertTrue(a and b)

if __name__ == '__main__':
    unittest.main(buffer=True)
