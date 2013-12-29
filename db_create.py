#!/usr/bin/env python

import csv
import os.path

from migrate.versioning import api

from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from CC2013 import app, db
from CC2013.models import *


def populate_from_csv():
    logging = app.config['DEBUG'] and app.config['CC2013_LOGGING']
    if Area.query.all():
        if logging:
            logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        return

    # Initialize Knowledge Areas (Area table)
    with open('csv/ka.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                id = row[0].strip().upper()
                text = row[1].strip()
                area = Area(id=id, text=text)
                db.session.add(area)
    db.session.commit()

    # Initialize Knowledge Units (Unit table)
    with open('csv/LearningOutcomes.csv') as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        area = None
        for row in reader:
            # Skip rows that can't hold a KU
            if len(row) < 6:
                continue
            #print row
            # Find the related KA from the database
            area_id = row[0].strip().upper()
            if area_id and (not area or area_id != area.id):
                area = Area.query.get(area_id)

            # CSV match is 6 or more fields with area_id and row[4] blank
            if area_id and not row[4].strip():
                text = row[1].strip()
                tier1 = float(row[2])
                tier2 = float(row[3])
                unit = Unit(area=area, text=text, tier1=tier1, tier2=tier2)
                db.session.add(unit)
    db.session.commit()

    # Initialize Learning Outcomes (Outcome table)
    with open('csv/LearningOutcomes.csv') as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        unit = None
        for row in reader:
            # CSV match is 6 or more fields with row[4] & row[5] non-blank
            if len(row) >= 6 and row[4] and row[5]:
                # Find the related KU from the database
                unit_text = row[1].strip()
                unit = Unit.query.filter_by(text=unit_text).first()

                tier = ['Tier 1', 'Tier 2', 'Elective'][int(row[2]) - 1]
                mastery = row[3].strip()
                number = int(row[4])
                text = row[5].strip()
                outcome = Outcome(unit=unit, tier=tier, mastery=mastery, number=number, text=text)
                db.session.add(outcome)
    db.session.commit()

    if logging:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    if app.config['DEBUG']:
        program = Program('CS Major [2014]', 'The Computer Science Major from the 2014-15 Academic Catalog')
        db.session.add(program)
        db.session.commit()
        course = Course(program, 'Discrete Mathematics', 'MTH 242', 'Sets, logic, proofs, etc.')
        db.session.add(course)
        db.session.commit()


# Create the database and initialize from csv data
db.create_all()

populate_from_csv()

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
