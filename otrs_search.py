#!/usr/bin/python
# -*- coding: utf8 -*-

import urllib, urlparse, httplib, sys, json, csv, tempfile, os, getpass, getopt, time, ConfigParser, ssl
from pyme import core, constants, errors

REQ = '/otrs/index.pl' #FIXME: In config file ?
OTRS_CONFIG = '~/.otrs-config'
OTRS_PASSWD = '~/.otrs-passwd'
OTRS_SESSION = '.otrs-session'

options = {
    'req_amount':    1,
    'req_unit':      'day',
    'req_ticketid':  '',
    'req_from':      '',
    'req_order':     'Up',
    #'req_queue':    '',
    #'req_state':    '',
    'uri_scheme':    'https',
    'flag_ssl':      True,
    'flag_google':   True,
    'flag_verbose':  False,
    'flag_fulltext': True,
}

def usage():
    print 'Usage: %s <request>\nMore information with: %s --help'%(sys.argv[0], sys.argv[0])
    sys.exit(0)

def help():
    print '''Usage: %s <request>
  with <requests> the request string to search. You can add multiple strings without protecting them with \'.
  You can use the logical operators AND and OR.
  -a, --amount\t\tAmount of unit to search for in creation date (default: 1)
  -u, --unit\t\tSearch unit for creation date. Possible values are: day, hour, minute, month, week, year (default: day)
  -g, --no-google\tDo not create short link to the ticket
  -r, --reverse\t\tReverse the result order (always sorted by date)
  -v, --verbose\t\tDisplay what is being done
  -h\t\t\tYou are reading it
  --id\t\t\tSearch ticket by id
  --from\t\tSearch by requestor (client or otrs agent) email
  --queue\t\tTODO: Search by queue name
  --state\t\tTODO: Search by ticket state. Possible values: 'new', 'open', 'closed' '''%sys.argv[0]

def shorten(url):
    conn = httplib.HTTPSConnection('www.googleapis.com')
    conn.request("POST", '/urlshortener/v1/url?key=%s&fields=id'%GOOKEY, '{"longUrl": "%s"}'%url, {'Content-Type': 'application/json'})
    data = json.loads(conn.getresponse().read())
    conn.close() # Use a connection pool or smth
    if 'id' in data:
        return str(data['id'])
    return '(goog.gl: %s)'%data['error']['message']

#def logged():
#    if flag_verbose:
#        print '\033[0;32mSession check\033[0m'
#    try:
#        conn = httplib.HTTPSConnection(HOST)
#        conn.request("GET", REQ, '', get_headers())
#        if conn.getresponse().getheader('Content-Disposition') != None:
#            return True
#    except Exception, e:
#        sys.exit(e)
#    return False

def get_session():
    try:
        f = open('%s/%s'%(tempfile.gettempdir(), OTRS_SESSION), 'r')
        session = f.read()
        f.close()
        return session
    except IOError, e:
        return ''

def get_headers():
    return {
        'User-agent': 'OTRS Search Script',
        'Content-type': 'application/x-www-form-urlencoded',
        'Cookie': get_session(),
    }

def create_session(force=False):
    if os.path.exists('%s/%s'%(tempfile.gettempdir(), OTRS_SESSION)) and not force:
        return
    if options['flag_verbose']:
        print '\033[0;32mSession creation\033[0m'
    authfile = os.path.expanduser(OTRS_PASSWD)
    sessfile = '%s/%s'%(tempfile.gettempdir(), OTRS_SESSION)
    try:
        os.remove(sessfile)
    except OSError, e:
        print e

    # Get crypted user/pass
    try:
        plain = core.Data()
        crypted = core.Data(open(authfile, 'r').read())
    except IOError, e:
        print 'Please create a password file with User=user&Password=password, encrypted with gnupg (%s)'%e
        sys.exit(e)
    # Decrypt user/pass
    c = core.Context()
    c.set_armor(1)
    c.set_passphrase_cb(passphrase_cb)
    try:
        c.op_decrypt(crypted, plain)
    except errors.GPGMEError, e:
        sys.exit(e)
    plain.seek(0, 0)
    # Send credential and get session token
    if options['flag_ssl']:
        conn = httplib.HTTPSConnection(HOST)
    else:
        conn = httplib.HTTPConnection(HOST)
    conn.request("POST", REQ, 'Action=Login&RequestedURL=Action%3DLogout&Lang=fr&TimeOffset=-60&'+plain.read(), get_headers())
    res = conn.getresponse()
    cookie = res.getheader('set-cookie')
    if cookie is not None:
        if options['flag_verbose']:
            print 'Creating %s with %s'%(sessfile, cookie)
        f = open(sessfile, 'w+')
        f.write(cookie)
        f.close()
    else:
        os.remove(authfile)
        sys.exit('Authentification failed, please recreate %s'%authfile)

def passphrase_cb(x,y,z):
    print 'Using key: %s'%x
    return getpass.getpass('Passphrase: ')

#def login_check():
#    if not logged():
#        if flag_verbose:
#            print '\033[0;31mYou are not logged in!\033[0m'
#        create_session()

def get_args(args):
    global options
    try:
        opts, reqs = getopt.gnu_getopt(args, 'rghva:u:', ['reverse', 'no-google', 'help', 'verbose', 'amount=', 'unit=', 'id', 'from='])
        options['req_body'] = ' '.join(reqs)
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                help()
                sys.exit(0)
            elif opt in ('-g', '--no-google'):
                options['flag_google'] = False
            elif opt in ('-r', '--reverse'):
                options['req_order'] = 'Down'
            elif opt in ('-v', '--verbose'):
                options['flag_verbose'] = True
            elif opt in ('-a', '--amount'):
                options['req_amount'] = arg
            elif opt in ('-u', '--unit'):
                options['req_unit'] = arg
            elif opt == '--id':
                options['req_ticketid'] = options['req_body']
                options['req_body'] = ''
                options['req_amount'] = ''
                options['req_unit'] = ''
                options['flag_fulltext'] = False
            elif opt == '--from':
                options['req_from'] = arg
                options['flag_fulltext'] = False
            #elif opt == '--queue':
            #    options['req_queue'] = arg
            #elif opt == '--state':
            #    options['req_state'] = 'open'
    except getopt.GetoptError:
        usage()

    if options['flag_verbose']:
        print 'Options in use: amount=%s, unit=%s'%(options['req_amount'], options['req_unit'])

    if len(args) < 1 and options['flag_fulltext']:
        usage()

# Get configuration
def get_conf():
    global HOST, GOOKEY, options
    options['flag_ssl'] = True
    options['uri_scheme'] = 'https'
    c = ConfigParser.RawConfigParser()
    c.read(os.path.expanduser(OTRS_CONFIG))
    try:
        HOST = c.get('Main', 'host')
        GOOKEY = c.get('Main', 'google_key')
        if '443' not in HOST:
            options['flag_ssl'] = False
            options['uri_scheme'] = 'http'
    except ConfigParser.NoSectionError, e:
        sys.exit('You must create a config file in %s (%s)'%(OTRS_CONFIG, e))

def get_tickets():
    # Construct POST request
    params = urllib.urlencode({
        'Body':                         options['req_body'],
        'TicketNumber':                 options['req_ticketid'],
        'From':                         options['req_from'],
        'Action':                       'AgentTicketSearch',
        'Subaction':                    'Search',
        'TimeSearchType':               'TimePoint',
        'TicketCreateTimePointStart':   'Last',
        'TicketCreateTimePoint':        options['req_amount'],
        'TicketCreateTimePointFormat':  options['req_unit'],
        'SortBy':                       'Age',
        'OrderBy':                      options['req_order'],
        #'Queues':                      options['req_queue'],
        #'StateType':                   options['req_state'],
        'ResultForm':                   'CSV',
    })

    # Get Tickets
    if options['flag_verbose']:
        print '\033[0;32mSearching tickets ...\033[0m'
    if options['flag_ssl']:
        conn = httplib.HTTPSConnection(HOST)
    else:
        conn = httplib.HTTPConnection(HOST)
    try:
        conn.request("POST", REQ, params, get_headers())
        res = conn.getresponse()
    except Exception, e:
        sys.exit(e)

    # Check response
    if res.getheader('Content-type') != 'text/csv; charset=utf-8':
        create_session(force=True)
        sys.exit('Session created, please make request again.')

    return res

def show_tickets(res):
    # Save result
    # TODO: Use filename given in http header
    csvdata = res.read()
    f = tempfile.mktemp()
    csvfile = open(f, 'w+')
    csvfile.write(csvdata)
    csvfile.seek(0)

    # Show tickets
    tickets_nb = 0
    tickets = {}
    if os.path.getsize(csvfile.name) > 1:
        tickets_nb = len(open(f, 'rb').readlines()) - 1
        tickets = csv.reader(csvfile, delimiter=';', quotechar='"')
        # Language dependent field number
        row = tickets.next()
        id_queue = 0
        id_title = 0
        id_state = 0
        # English
        if row[2] == 'Created':
            id_queue = row.index('Queue')
            id_title = row.index('Subject')
            id_state = row.index('State')
        # French
        elif row[2] == 'Créé':
            id_queue = row.index('File')
            id_title = row.index('Sujet')
            id_state = row.index('État')

    print '\033[0;31mTicket(s) number: %i\033[0m'%tickets_nb

    if tickets_nb == 0:
        csvfile.close()
        os.remove(csvfile.name)
        sys.exit(0)

    for row in tickets:
        try:
            ticketid = str(row[0])
            date     = str(row[2])
            queue    = str(row[id_queue])
            title    = str(row[id_title])
            link     = ''
            state    = ''
            if row[id_state]=='open' or row[id_state]=='new':
                state = '\033[1;31m[%s] \033[0m'%str(row[id_state]).upper()
        except IndexError, e:
            print row
            sys.exit(e)
        link = '%s://%s%s?Action=AgentTicketZoom&TicketNumber=%s&ZoomExpand=1'%(options['uri_scheme'], HOST, REQ, int(ticketid))
        if options['flag_google']:
            link = shorten(link)
        try:
            print '\033[0;32m%s \033[0;34m%s \033[0;33m[%s] %s\033[0m\033[1m%s\033[0m\033[0m %s\033[0m'%(date, ticketid, queue, state, title, link)
        except UnicodeDecodeError, e:
            print 'ticketid = %s : %s'%(ticketid,e)

    csvfile.close()

    print 'CSV: %s'%f

if __name__ == '__main__':
    get_args(sys.argv[1:])
    get_conf()
    create_session()
    res = get_tickets()
    show_tickets(res)

