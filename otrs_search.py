#!/usr/bin/python
# -*- coding: utf8 -*-

import urllib, urlparse, httplib, sys, json, csv, tempfile, os, getpass, getopt, time, ConfigParser
from pyme import core, constants, errors

REQ = '/otrs/index.pl' #FIXME: In config file ?
OTRS_CONFIG = '~/.otrs-config'
OTRS_PASSWD = '~/.otrs-passwd'
OTRS_SESSION = '.otrs-session'

def usage():
    print 'Usage: %s <request>\nPour plus d\'informations: %s --help'%(sys.argv[0], sys.argv[0])
    sys.exit(0)

def help():
    print '''Usage: %s <request>
  with <requests> the request string to search. You can add multiple strings without protecting them with \'.
  You can use the logical operators AND and OR. 
  -a, --amount\t\tAmount of unit to search for in creation date (default: 1)
  -u, --unit\t\tSearch unit for creation date. Possible values are: day, hour, minute, month, week, year (default: day)
  -g, --no-google\t\tDo not create short link to the ticket
  -r, --reverse\t\tReverse the result order (always sorted by date)
  -v, --verbose\t\tDisplay what is being done
  -h\t\t\tYou are reading it
   --id\t\t\tSearch ticket by id
  --client\t\tSearch by customer email
  --queue\t\tTODO: Search by queue name
  --state\t\tTODO: Search by ticket state. Possible values: 'new', 'open', 'closed' '''

def shorten(url):
    conn = httplib.HTTPSConnection('www.googleapis.com')
    conn.request("POST", '/urlshortener/v1/url?key=%s&fields=id'%GOOKEY, '{"longUrl": "%s"}'%url, {'Content-Type': 'application/json'})
    data = json.loads(conn.getresponse().read())
    conn.close() # Use a connection pool or smth
    if 'id' in data:
        return data['id']
    return '(goog.gl: %s)'%data['error']['message']

#def logged():
#    if verbose:
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
        return session
    except IOError, e:
        return ''

def get_headers():
    return {
        'User-agent': 'OTRS 2.3.4 Search Script',
        'Content-type': 'application/x-www-form-urlencoded',
        'Cookie': get_session(),
    }

def create_session():
    if verbose:
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
    conn = httplib.HTTPSConnection(HOST)
    conn.request("POST", REQ, 'Action=Login&RequestedURL=Action%3DLogout&Lang=fr&TimeOffset=-60&'+plain.read(), get_headers())
    res = conn.getresponse()
    cookie = res.getheader('set-cookie')
    if cookie is not None:
        if verbose:
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
#        if verbose: 
#            print '\033[0;31mYou are not logged in!\033[0m'
#        create_session()

##########
## Main

# Get arguments
req_amount = 1
req_unit = 'day'
req_ticketid = ''
req_from = ''
req_order = 'Up'
#req_queue = ''
#req_state = ''
google = True
verbose = False
fulltext = True
try:
    opts, args = getopt.getopt(sys.argv[1:], 'rghva:u:', ['reverse', 'no-google', 'help', 'verbose', 'amount=', 'unit=', 'id', 'client='])
    req_body = ' '.join(args)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help()
            sys.exit(0)
        elif opt in ('-g', '--no-google'):
            google = False
        elif opt in ('-r', '--reverse'):
            req_order = 'Down'
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt in ('-a', '--amount'):
            req_amount = arg
        elif opt in ('-u', '--unit'):
            req_unit = arg
        elif opt == '--id':
            req_ticketid = req_body
            req_body = ''
            req_amount = ''
            req_unit = ''
            fulltext = False
        elif opt == '--client':
            req_from = arg
            fulltext = False
        #elif opt == '--queue':
        #    req_queue = arg
        #elif opt == '--state':
        #    req_state = 'open'
except getopt.GetoptError:
    usage()

if verbose:
    print 'Options in use:\n amount=%s, unit=%s'%(req_amount, req_unit)

if len(args) < 1 and fulltext:
    usage()

# Get configuration
c = ConfigParser.RawConfigParser()
c.read(os.path.expanduser(OTRS_CONFIG))
try:
    HOST = c.get('Main', 'host')
    GOOKEY = c.get('Main', 'google_key')
except ConfigParser.NoSectionError, e:
    sys.exit('You must create a config file in %s (%s)'%(OTRS_CONFIG, e))

# Create session
if not os.path.exists('%s/%s'%(tempfile.gettempdir(), OTRS_SESSION)):
    create_session()

# Search query
params = urllib.urlencode({
    'Body': req_body,
    'TicketNumber': req_ticketid,
    'From': req_from,
    'Action': 'AgentTicketSearch',
    'Subaction': 'Search',
    'TimeSearchType': 'TimePoint',
    'TicketCreateTimePointStart': 'Last',
    'TicketCreateTimePoint': req_amount,
    'TicketCreateTimePointFormat': req_unit,
    'SortBy': 'Age',
    'Order': req_order,
    #'Queues': req_queue,
    #'StateType': req_state,
    'ResultForm': 'CSV',
})

# Get Tickets
if verbose:
    print '\033[0;32mSearching tickets ...\033[0m'
conn = httplib.HTTPSConnection(HOST)
conn.request("POST", REQ, params, get_headers())
res = conn.getresponse()

# Check response
if res.getheader('Content-type') != 'text/csv; charset=utf-8':
    create_session()
    sys.exit('Session created, please make request again.')

# Save result
# TODO: Use filename given in http header
csvdata = res.read()
f = tempfile.mktemp()
csvfile = open(f, 'w+')
csvfile.write(csvdata)
csvfile.seek(0)

# Show tickets
tickets_nb = len(open(f, 'rb').readlines()) - 1
tickets = csv.reader(csvfile, delimiter=';', quotechar='"')
tickets.next() # Skip first line
print '\033[0;31mTicket(s) number: %i\033[0m'%tickets_nb
for row in tickets:
    try:
        ticketid = row[0]
        queue = unicode(row[5], 'utf8')
        title = unicode(row[13], 'utf8')
        date = row[2]
        link = ''
        state = ''
        if row[3]=='open' or row[3]=='new':
            state = '\033[1;31m[%s] \033[0m'%row[3].upper()
    except IndexError, e:
        print row
        sys.exit(e)
    if google:
        link = shorten('https://%s%s?Action=AgentTicketZoom&TicketNumber=%s&ZoomExpand=1'%(HOST, REQ, int(ticketid)))
    try:
        print '\033[0;32m%s \033[0;34m%s \033[0;33m[%s] %s\033[0m\033[1m%s\033[0m\033[0m %s\033[0m'%(date, ticketid, queue, state, title, link)
    except UnicodeDecodeError, e:
        print e, row

print 'CSV: file://%s'%f

