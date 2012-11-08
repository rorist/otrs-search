#!/usr/bin/python
# -*- coding: utf8 -*-

from BeautifulSoup import BeautifulSoup
import urllib, urlparse, httplib, sys, json, csv, tempfile, os, getpass, getopt
import time, ConfigParser, ssl, codecs, re
from pyme import core, constants, errors

REQ = '/otrs/index.pl' #FIXME: In config file ?
OTRS_CONFIG = '~/.otrs-config'
OTRS_PASSWD = '~/.otrs-passwd'
OTRS_SESSION = '.otrs-session'
QUEUES = {}

options = {
    'req_amount':    1,
    'req_unit':      'day',
    'req_ticketid':  '',
    'req_from':      '',
    'req_client':    '',
    'req_order':     'Up',
    #'req_state':    '',
    'uri_scheme':    'https',
    'flag_ssl':      True,
    'flag_google':   True,
    'flag_verbose':  False,
}

def usage():
    pth = os.path.basename(sys.argv[0])
    print 'Usage: %s <request>\nMore information with: %s --help'%(pth, pth)
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
  -q, --queue\t\tSearch by queue name/IDs, it machtes the first queue, case insensitive
  -Q, --queues\t\tList queues name/IDs
  -h\t\t\tYou are reading it
  --id\t\t\tSearch ticket by id
  --client\t\tSearch by Client ID
  --from\t\tSearch by requestor (client or otrs agent) email
  --state\t\tTODO: Search by ticket state. Possible values: 'new', 'open', 'closed', 'merged', 'pending', 'removed' '''%os.path.basename(sys.argv[0])

def debug(message):
    if options['flag_verbose']:
        print '\033[0;30m--%s\033[0m'%message

def shorten(url):
    conn = httplib.HTTPSConnection('www.googleapis.com')
    conn.request("POST", '/urlshortener/v1/url?key=%s&fields=id'%GOOKEY, '{"longUrl": "%s"}'%url, {'Content-Type': 'application/json'})
    data = json.loads(conn.getresponse().read())
    conn.close() # Use a connection pool or smth
    if 'id' in data:
        return data['id']
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
    debug('Get session')
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
    debug('Session creation')
    authfile = os.path.expanduser(OTRS_PASSWD)
    sessfile = '%s/%s'%(tempfile.gettempdir(), OTRS_SESSION)
    try:
        os.remove(sessfile)
    except OSError, e:
        print e

    debug('Decrypt password')
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
        print '\033[0;31mGPG error: reading password in plain text\033[0m'
        plain = core.Data(open(authfile, 'r').read())
    plain.seek(0, 0)
    # Send credential and get session token
    debug('Login attempt')
    if options['flag_ssl']:
        conn = httplib.HTTPSConnection(HOST)
    else:
        conn = httplib.HTTPConnection(HOST)
    conn.request("POST", REQ, 'Action=Login&RequestedURL=Action%3DLogout&Lang=fr&TimeOffset=-60&'+plain.read(), get_headers())
    res = conn.getresponse()
    cookie = res.getheader('set-cookie')
    if cookie is not None:
        debug('Creating %s with %s'%(sessfile, cookie))
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
    debug('Process arguments')
    try:
        opts, reqs = getopt.gnu_getopt(args, 'rghva:u:Qq:', ['reverse', 'no-google',
                                                           'help', 'verbose',
                                                           'amount=', 'unit=',
                                                           'id', 'from=', 'queues',
                                                           'queue=', 'client='])
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
            elif opt == '--from':
                options['req_from'] = arg
            elif opt == '--client':
                options['req_client'] = arg
            elif opt in ('--queues', '-Q'):
                create_session()
                get_queues()
                for k in QUEUES:
                    print k[0], k[1]
                sys.exit(0)
            elif opt in ('--queue', '-q'):
                create_session()
                get_queues()
                if arg in [i[0] for i in QUEUES]:
                    options['req_queue'] = arg
                else:
                    a = [i[0] for i in QUEUES if re.match('.*'+arg.lower()+'.*', i[1].lower()) != None]
                    if len(a) > 0:
                        options['req_queue'] = a[0]
            #elif opt == '--state':
            #    options['req_state'] = 'open'
    except getopt.GetoptError:
        usage()

    if len(args) < 1:
        usage()

# Get configuration
def get_conf():
    global HOST, GOOKEY, options
    debug('Get configuration from file')
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
    debug('Get tickets list')
    # Construct POST request
    params = {
        'Body':                         options['req_body'],
        'TicketNumber':                 options['req_ticketid'],
        'From':                         options['req_from'],
        'CustomerID':                   options['req_client'],
        'Action':                       'AgentTicketSearch',
        'Subaction':                    'Search',
        'TimeSearchType':               'TimePoint',
        'TicketCreateTimePointStart':   'Last',
        'TicketCreateTimePoint':        options['req_amount'],
        'TicketCreateTimePointFormat':  options['req_unit'],
        'SortBy':                       'Age',
        'OrderBy':                      options['req_order'],
        #'StateType':                   options['req_state'],
        'ResultForm':                   'CSV',
    }
    if 'req_queue' in options:
        params['QueueIDs'] = options['req_queue']
    params = urllib.urlencode(params)

    # Get Tickets
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

def get_queues():
    global QUEUES
    debug('Get queues list')
    if len(QUEUES) > 0:
        return
    if options['flag_ssl']:
        conn = httplib.HTTPSConnection(HOST)
    else:
        conn = httplib.HTTPConnection(HOST)
    try:
        conn.request("POST", REQ, urllib.urlencode({
            'Action': 'AgentTicketSearch',
            'Subaction': 'AJAX'}), get_headers())
        res = conn.getresponse()
    except Exception, e:
        sys.exit(e)
    soup = BeautifulSoup(res.read())
    QUEUES = []
    for queue in soup.find('select', {'name': 'QueueIDs'}).findAll('option'):
        QUEUES.append([str(queue.get('value')), queue.getText().replace('&nbsp;', '-')])

def show_tickets(res):
    debug('Show tickets')
    # Save result
    # TODO: Use filename given in http header
    csvdata = res.read()
    f = tempfile.mktemp()
    csvfile = open(f, 'w+')
    csvfile.write(csvdata)
    csvfile.seek(0)

    # Show tickets
    tickets_nb = 0
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

    if 'req_queue' in options:
        print '\033[0;31m%i ticket(s) in %s\033[0m'%(
            tickets_nb, [i[1].replace('-', '') for i in QUEUES if i[0]==options['req_queue']][0])
    else:
        print '\033[0;31m%i ticket(s)\033[0m'%tickets_nb

    if tickets_nb == 0:
        csvfile.close()
        os.remove(csvfile.name)
        sys.exit(0)

    for row in tickets:
        try:
            ticketid = row[0]
            date     = row[2].decode('utf-8')
            queue    = row[id_queue].decode('utf-8')
            title    = row[id_title].decode('utf-8')
            link     = ''
            state    = ''
            if row[id_state]=='open' or row[id_state]=='new':
                state = '\033[1;31m[%s] \033[0m'%row[id_state].upper().decode('utf-8')
        except IndexError, e:
            print row
            sys.exit(e)
        link = '%s://%s%s?Action=AgentTicketZoom&TicketNumber=%s&ZoomExpand=1'%(
            options['uri_scheme'], HOST, REQ, int(ticketid))
        if options['flag_google']:
            link = shorten(link)
        try:
            print '\033[0;32m%s \033[0;34m%s \033[0;33m[%s] %s\033[0m\033[1m%s\033[0m\033[0m %s\033[0m'%(
                date, ticketid, queue, state, title, link)
        except UnicodeEncodeError, e:
            print 'ticketid = %s : %s'%(ticketid,e)

    csvfile.close()

    print 'CSV: %s'%f

if __name__ == '__main__':
    UTF8Writer = codecs.getwriter('utf8')
    sys.stdout = UTF8Writer(sys.stdout)
    get_conf()
    get_args(sys.argv[1:])
    create_session()
    res = get_tickets()
    show_tickets(res)

