#!/usr/bin/env python
import unittest
import otrs_search
import os, sys, re, tempfile, csv
import logging

class TestSearch(unittest.TestCase):

    def test_conf(self):
        otrs_search.get_conf()
        self.assertNotEqual(otrs_search.HOST, '')

    def test_login(self):
        sessfile = os.path.expanduser(otrs_search.OTRS_SESSION)
        os.remove(sessfile)
        otrs_search.get_conf()
        otrs_search.create_session()
        self.assertTrue(os.path.exists(sessfile))

    def test_queues(self):
        args = ['-Q']
        try:
            otrs_search.get_args(args)
        except SystemExit, e:
            out = sys.stdout.getvalue().split('\n')[:-1]
            for l in out:
                self.assertIsNotNone(re.match('^\d{1,3} [\ \.\-_0-9a-zA-Z]*$', l.encode('ascii', 'ignore')))
            self.assertEquals(e.code, 0)
        else:
            self.fail('SystemExit expected')

    def test_custom_csv(self):
        args = ['--csv', './test_data.csv', '-n']
        otrs_search.get_args(args)
        csvfile = open('./test_data.csv', 'rb')
        otrs_search.show_tickets(csvfile)
        lines = sys.stdout.getvalue().split('\n')
        self.assertEquals(len(lines), 6)

    def test_date_format(self):
        args = ['-n', '-f', 'YYYY-MM-DD ']
        otrs_search.get_args(args)
        res = otrs_search.get_tickets()
        csvfile = otrs_search.write_data(res)
        otrs_search.show_tickets(csvfile)
        lines = sys.stdout.getvalue().split('\n')
        #log = logging.getLogger( "TEST" )
        for l in lines[1:-2]:
            #log.debug( "l=%r", l)
            r = re.match(u'^\x1b\[0;32m\d{4}-\d{2}-\d{2} \x1b\[0;34m\d{7}', l)
            self.assertNotEqual(r, None)

#    def test_stuff(self):
#        args = ['-n']
#        otrs_search.get_args(args)
#        res = otrs_search.get_tickets()
#        csvdata = csv.reader(res.read().split('\n'), delimiter=';', quotechar='"')
#        csvdata.next()
#        for i in csvdata:
#            print i

    def test_queue_id(self):
        args = ['-q', '1', '-u', 'week', '-a', '1', '-g']
        self.search(args)

    def test_queue_name(self):
        args = ['-q', 'a', '-u', 'week', '-a', '1', '-g']
        self.search(args)

    def test_search_basic(self):
        args = ['-a', '1', '-u', 'week', '-g']
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
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "TEST" ).setLevel( logging.DEBUG )
    unittest.main(buffer=True)
