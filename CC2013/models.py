import csv
from hashlib import md5
import os.path

from CC2013 import app, db


__all__ = ['User', 'Area', 'Unit', 'Outcome', 'Program', 'Course', 'course_units', 'ROLE_USER', 'ROLE_ADMIN']


class Area(db.Model):
    '''A "Knowledge Area", as defined in CC2013.

    These high-level areas divide the entire Body of Knowledge (BOK).'''
    id = db.Column(db.String(3), primary_key=True)
    text = db.Column(db.String(64))
    units = db.relationship('Unit', backref='area', lazy='dynamic')

    def __init__(self, id, text):
        self.id = id.strip().upper()
        self.text = text.strip()

    def __repr__(self):
        return '<Knowledge Area: {0.id:>3s}>'.format(self)


class Unit(db.Model):
    '''A "Knowledge Unit", as defined in CC2013.

    These subdivisions represent key aspects of their related "Knowledge Areas".'''
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(64))
    tier1 = db.Column(db.Float)
    tier2 = db.Column(db.Float)
    elective = db.Column(db.Float)
    area_id = db.Column(db.String, db.ForeignKey('area.id', ondelete='cascade'))
    outcomes = db.relationship('Outcome', backref='unit', lazy='dynamic')

    def __init__(self, area, text, tier1, tier2):
        self.area_id = area.id
        self.text = text.strip()
        self.tier1 = tier1
        self.tier2 = tier2

    def __repr__(self):
        return '<Knowledge Unit: "{0.text}" KA: {0.area} Hours: ({0.tier1}, {0.tier2})>'.format(self)


class Outcome(db.Model):
    '''A "Learning Outcome", as defined in CC2013.'''
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300))
    tier = db.Column(db.Enum('Tier 1', 'Tier 2', 'Elective', name='outcome_tier'))
    mastery = db.Column(db.Enum('Familiarity', 'Usage', 'Assessment', name='outcome_mastery'))
    number = db.Column(db.Integer)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id', ondelete='cascade'))

    def __init__(self, unit, tier, mastery, number, text):
        self.unit_id = unit.id
        self.tier = tier
        self.mastery = mastery
        self.number = number
        self.text = text.strip()

    def __repr__(self):
        return '<Outcome: {0.number:2d}. {0.text} Tier: {0.tier} Mastery: {0.mastery} {0.unit}>'.format(self)


ROLE_USER = 0
ROLE_ADMIN = 1


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    programs = db.relationship('Program', backref='user', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname = nickname).first() == None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname = new_nickname).first() == None:
                break
            version += 1
        return new_nickname

    def avatar(self, size=128):
        hash = md5(self.email).hexdigest()
        return 'http://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(hash, size)

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def __repr__(self):
        return '<User {0.nickname}>'.format(self)


class Program(db.Model):
    '''A collection of courses built to cover "Learning Outcomes".'''
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), unique=True)
    description = db.Column(db.String)
    courses = db.relationship('Course', backref='program', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='cascade'))

    def __init__(self, user, title, description=None):
        self.user_id = user.id
        self.title = title
        self.description = description

    def __repr__(self):
        return '<Program: {0.title}>'.format(self)


course_units = db.Table('course_units',
                        db.Column('course_id', db.Integer, db.ForeignKey('course.id')),
                        db.Column('unit_id', db.Integer, db.ForeignKey('unit.id')))


class Course(db.Model):
    '''A member of a program built to cover "Learning Outcomes".'''
    id = db.Column(db.Integer, primary_key=True)
    abbr = db.Column(db.String(8))
    title = db.Column(db.String(128))
    description = db.Column(db.String)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id', ondelete='cascade'))
    units = db.relationship('Unit', secondary=course_units,
                            backref=db.backref('courses', lazy='dynamic'))

    def __init__(self, program, title, abbr=None, description=None):
        self.program_id = program.id
        self.title = title
        self.abbr = abbr
        self.description = description

    def __repr__(self):
        return '<Course: {0.abbr} - {0.title} {0.program}>'.format(self)


# Initialize the database
#@app.before_first_request
def init_db():
    db.create_all()
    logging = app.config['DEBUG'] and app.config['_LOGGING']
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
                area = Area(id, text)
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
                area = Area.query.filter_by(id=area_id).first()

            # CSV match is 6 or more fields with area_id and row[4] blank
            if area_id and not row[4].strip():
                text = row[1].strip()
                tier1 = float(row[2])
                tier2 = float(row[3])
                unit = Unit(area, text, tier1, tier2)
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
                outcome = Outcome(unit, tier, mastery, number, text)
                db.session.add(outcome)
    db.session.commit()

    if logging:
        program = Program('CS Major [2014]', 'The Computer Science Major from the 2014-15 Academic Catalog')
        db.session.add(program)
        db.session.commit()
        course = Course(program, 'Discrete Mathematics', 'MTH 242', 'Sets, logic, proofs, etc.')
        db.session.add(course)
        db.session.commit()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
