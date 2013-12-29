#!/usr/bin/env python

import os
import sys


os.system('pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot CC2013')
os.system('pybabel update -i messages.pot -d CC2013/translations')
os.unlink('messages.pot')
