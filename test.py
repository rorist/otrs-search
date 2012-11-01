#!/usr/bin/env python
import unittest
import otrs_search
import os, tempfile

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

if __name__ == '__main__':
        unittest.main()

#get_args(sys.argv[1:])
#res = get_tickets()
#show_tickets(res)
