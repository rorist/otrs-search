#!/usr/bin/env python
from setuptools import setup
import sys, shutil

try:
    import pyme
except Exception as e:
    print 'You need to install the python-pyme package'
    sys.exit()


setup(
    name =              "otrs_search",
    version =           "1.0",
    author =            "Aubort Jean-Baptiste",
    author_email =      "jeanbaptiste.aubort@gmail.com",
    description =       ("Command line search script for the OTRS 2.x ticketing system, using https/http resquests in python. Password is encrypted with GnuPG. Support English and French languages"),
    long_description =  open('README.md').read(),
    license =           "gpl-3.0.txt",
    keywords =          "otrs search command line",
    url =               "https://github.com/jbaubort/otrs-search",
    classifiers =       [
        'Environment :: Console',
        'Topic :: Internet :: WWW/HTTP',
        'Development Status :: 5 - Production/Stable',
    ],
    py_modules =        ['otrs_search'],
    scripts =           ['otrs_search.py'],
    requires =  ['pyme', 'BeautifulSoup'],
)

shutil.rmtree('build', ignore_errors=True)
shutil.rmtree('dist', ignore_errors=True)
shutil.rmtree('otrs_search.egg-info', ignore_errors=True)

print
print '\033[1mPlease run ./create_config.py to create configuration files\033[0m'
print
