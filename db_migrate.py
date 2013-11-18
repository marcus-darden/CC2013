#!/usr/bin/env python

import imp
import os.path

from migrate.versioning import api

from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from CC2013 import db


new_version = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO) + 1
migration = os.path.join(SQLALCHEMY_MIGRATE_REPO,
                         'versions/{:03d}_migration.py'.format(new_version))
tmp_module = imp.new_module('old_model')
old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
exec old_model in tmp_module.__dict__
script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI,
                                          SQLALCHEMY_MIGRATE_REPO,
                                          tmp_module.meta,
                                          db.metadata)
with open(migration, 'wt') as f:
    f.write(script)
api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)

# Report the results
print 'New migration saved as ' + migration
version = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print 'Current database version: {}'.format(version)
