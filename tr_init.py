#!/usr/bin/env python

import os
import sys


if len(sys.argv) != 2:
    print 'usage: tr_init <language-code>'
    sys.exit(1)

os.system('pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot CC2013')
os.system('pybabel init -i messages.pot -d CC2013/translations -l ' + sys.argv[1])
os.unlink('messages.pot')
