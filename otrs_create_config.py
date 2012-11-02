#!/usr/bin/python

import os, sys, getpass, ConfigParser
from pyme import core, constants, errors

OTRS_CONFIG = '~/.otrs-config'
OTRS_PASSWD = '~/.otrs-passwd'

# Encrypted password file creation
print 'Creating encrypted password file ...'
sys.stdout.write("GPG Key ID: ")
keyid = sys.stdin.readline().strip()
sys.stdout.write('OTRS Username: ')
username = sys.stdin.readline().strip()
password = getpass.getpass()

if username=='' or password=='' or keyid=='':
    print 'You must provide a username/password/keyID'
    sys.exit(1)

plain = core.Data('User=%s&Password=%s'%(username,password))
cipher = core.Data()

c = core.Context()
c.set_armor(0)

c.op_keylist_start(keyid, 0)
r = c.op_keylist_next()

try:
    c.op_encrypt([r], 1, plain, cipher)
    cipher.seek(0, 0)
    crypted = cipher.read()
except errors.GPGMEError, e:
    print 'Invalid key: %s'%e
    print '\033[0;31mUsing plain text password instead!\033[0m]]'
    crypted = plain

filename = os.path.expanduser(OTRS_PASSWD)
f = open(filename, 'w+')
f.write(crypted)
f.close()
print 'OTRS password file successfully written to %s!'%filename

# Configuration file
print 'Creating configuration file' #TODO Encrypt too ?
sys.stdout.write('OTRS Host (example.com:443): ')
host = sys.stdin.readline().strip()
sys.stdout.write('Google Shortener API Key (may be empty): ')
gookey = sys.stdin.readline().strip()
c = ConfigParser.RawConfigParser()
c.add_section('Main')
c.set('Main', 'host', host)
c.set('Main', 'google_key', gookey)
with open(os.path.expanduser(OTRS_CONFIG), 'wb') as configfile:
    c.write(configfile)
print 'OTRS config file successfully written to %s!'%OTRS_CONFIG
