Command Line search for OTRS 2.x
==================================

Command line search script for the OTRS 2.x ticketing system, using https resquests in python. Password is encrypted with GnuPG.

DEPENDENCIES
------------
- Python 2.6/2.7 (not compatible with Python 3)
- apt-get install python-pyme #http://pyme.sourceforge.net/

INSTALLATION
------------
- You must have a GPG key to create the password file

    $ gpg --gen-key

- Create config and password files,

    $ python otrs_create_config.py

FEATURES
--------
- Full text search
- Search by: id, client
- Time units and amount support (year, month, ...)
- English and French supported
- URL shortener using goog.gl (with token support)
- GPG encrypted password file
- Authenticate once until reboot (uses session cookie)
- Tested on OTRS 2.3.4 and 2.4.9

TODO
----
- Search by: queue name, state
- Use filename in header to save CSV file
- More stuff in configuration file

EXAMPLES
--------
    $ ./otrs_search.py --client dupont
    $ ./otrs_search.py --id 1234567
    $ ./otrs_search.py term1 AND term2

CHANGELOG
---------
- 08.11.11 JBA Creation du script, recherche basique
- 09.11.11 JBA Gestion des sessions 
- 16.11.11 JBA Search by Ticket ID or client email 
- 18.11.11 JBA Config is in a separate file, ready for publishing
- 22.11.11 JBA No google url shortener links option, missing translation
- 12.11.11 JBA Faster: do not check session with http but relying on session file.
- 20.12.11 JBA Reverse result option
- 12.01.12 JBA Add colored ticket state
- 13.01.12 JBA Support English !!!

LICENSE
-------
    
    Copyright (C) 2011 Jean-Baptiste Aubort <jean-baptiste.aubort@epfl.ch>

    This program is free software; you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 3 of the License, or any later
    version. This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
    Public License for more details. You should have received a copy of the
    GNU General Public License along with this program; if not, write to the
    Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

See gpl-3.0.txt
