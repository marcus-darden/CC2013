import csv
from hashlib import md5
import os.path
import re

from flask.ext.whooshalchemy import whoosh_index

from CC2013 import app, db


__all__ = ['User', 'Area', 'Unit', 'Outcome', 'Program', 'Course', 'course_units', 'ROLE_USER', 'ROLE_ADMIN']


class Area(db.Model):
    '''A "Knowledge Area", as defined in CC2013.

    These high-level areas divide the entire Body of Knowledge (BOK).'''
    __searchable__ = ['text']
    id = db.Column(db.String(3), primary_key=True)
    text = db.Column(db.String(64))
    units = db.relationship('Unit', backref='area', lazy='dynamic')

    def __repr__(self): # pragma: no cover
        return '<Knowledge Area: {0.id:>3s}>'.format(self)

    def json(self):
        return {'id': self.id,
                'text': self.text}


class Unit(db.Model):
    '''A "Knowledge Unit", as defined in CC2013.

    These subdivisions represent key aspects of their related "Knowledge Areas".'''
    __searchable__ = ['text']
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(64))
    tier1 = db.Column(db.Float)
    tier2 = db.Column(db.Float)
    elective = db.Column(db.Float)
    area_id = db.Column(db.String(3), db.ForeignKey('area.id', ondelete='cascade'))
    outcomes = db.relationship('Outcome', backref='unit', lazy='dynamic')

    def __repr__(self): # pragma: no cover
        return '<Knowledge Unit: "{0.text}" Hours: ({0.tier1}, {0.tier2}) {0.area}>'.format(self)

    def json(self):
        return {'tier1': self.tier1,
                'tier2': self.tier2,
                'text': self.text,
                'id': self.id,
                'area_id': self.area_id}


class Outcome(db.Model):
    '''A "Learning Outcome", as defined in CC2013.'''
    __searchable__ = ['text']
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(512))
    tier = db.Column(db.Enum('Tier 1', 'Tier 2', 'Elective', name='outcome_tier'))
    mastery = db.Column(db.Enum('Familiarity', 'Usage', 'Assessment', name='outcome_mastery'))
    number = db.Column(db.Integer)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id', ondelete='cascade'))

    def __repr__(self): # pragma: no cover
        return '<Outcome: {0.number:2d}. {0.text} Tier: {0.tier} Mastery: {0.mastery} {0.unit}>'.format(self)

    def json(self):
        return {'id': self.id,
                'text': self.text,
                'tier': self.tier,
                'mastery': self.mastery}


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

    def add_program(self, program):
        if not self.has_program(program):
            self.programs.append(program)
            return self

    def remove_program(self, program):
        if self.has_program(program):
            self.programs.remove(program)
            return self

    def has_program(self, program):
        return self.programs.filter(Program.id == program.id).count() > 0

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() == None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname = new_nickname).first() == None:
                break
            version += 1
        return new_nickname

    @staticmethod
    def make_valid_nickname(nickname):
        return re.sub('[^a-zA-Z0-9_\.]', '', nickname)

    def avatar(self, size=128):
        hash = md5(self.email).hexdigest()
        return 'https://secure.gravatar.com/avatar/{}?d=identicon&s={}'.format(hash, size)

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def __repr__(self): # pragma: no cover
        return '<User {0.nickname}>'.format(self)


class Program(db.Model):
    '''A collection of courses built to cover "Learning Outcomes".'''
    __searchable__ = ['title', 'description']
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), unique=True)
    description = db.Column(db.String(512))
    courses = db.relationship('Course', backref='program', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='cascade'))

    def add_course(self, course):
        if not self.has_course(course):
            self.courses.append(course)
            return self

    def remove_course(self, course):
        if self.has_course(course):
            self.courses.remove(course)
            return self

    def has_course(self, course):
        return self.courses.filter(Course.id == course.id).count() > 0

    @staticmethod
    def all_tier1_hours():
        return (db.session.query(db.func.sum(Unit.tier1))
                          .first())[0]

    @staticmethod
    def all_tier2_hours():
        return (db.session.query(db.func.sum(Unit.tier2))
                          .first())[0]

    @property
    def core_subquery(self): # pragma: no cover
        return (Unit.query
                    .join(Unit.courses, Course.program)
                    .filter(Program.id == self.id)
                    .subquery())

    @property
    def tier1_hours(self):
        return (db.session.query(db.func.sum(self.core_subquery.c.tier1))
                          .first())[0] or 0

    @property
    def tier2_hours(self):
        return (db.session.query(db.func.sum(self.core_subquery.c.tier2))
                          .first())[0] or 0

    def get_unassigned_units(self, area_id=None):
        program_courses = self.courses.statement.alias()
        program_units = (Unit.query
                             .with_entities(Unit.id)
                             .join(course_units)
                             .join(program_courses)
                             .all())
        unassigned_units = (Unit.query
                                .filter(Unit.id.notin_(program_units))
                                .order_by(Unit.id))

        if area_id:
            unassigned_units = unassigned_units.filter(Unit.area_id == area_id)

        return unassigned_units

    def content_coverage(self):
        data = [(c.abbr or c.title, c.tier1_hours, c.tier2_hours) for c in self.courses]
        titles, tier1_hours, tier2_hours = zip(*data)

        return titles, tier1_hours, tier2_hours

    def __repr__(self): # pragma: no cover
        return '<Program: {0.title}>'.format(self)


course_units = db.Table('course_units',
                        db.Column('course_id', db.Integer, db.ForeignKey('course.id')),
                        db.Column('unit_id', db.Integer, db.ForeignKey('unit.id')))


class Course(db.Model):
    '''A member of a program built to cover "Learning Outcomes".'''
    __searchable__ = ['title', 'description']
    id = db.Column(db.Integer, primary_key=True)
    abbr = db.Column(db.String(8))
    title = db.Column(db.String(128))
    description = db.Column(db.String(512))
    program_id = db.Column(db.Integer, db.ForeignKey('program.id', ondelete='cascade'))
    units = db.relationship('Unit', secondary=course_units,
                            backref=db.backref('courses', lazy='dynamic'),
                            order_by='Unit.id')

    def add_unit(self, unit):
        app.logger.info('Add Unit called ' + str(unit))
        app.logger.info('Course units: ' + str(self.units))
        if not self.has_unit(unit):
            self.units.append(unit)
            return self

    def remove_unit(self, unit):
        if self.has_unit(unit):
            self.units.remove(unit)
            return self

    def has_unit(self, unit):
        return unit in self.units

    @property
    def outcomes(self):
        return (Outcome.query.join(Outcome.unit, Unit.courses)
                       .filter(Course.id == self.id)
                       .order_by(Outcome.mastery, Outcome.tier, Outcome.id)
                       .all())

    @property
    def tier1_hours(self):
        if len(self.units) == 0:
            return 0
        return (db.session.query(db.func.sum(Unit.tier1))
                          .join(Unit.courses)
                          .filter(Course.id == self.id)
                          .first())[0]

    @property
    def tier2_hours(self):
        if len(self.units) == 0:
            return 0
        return (db.session.query(db.func.sum(Unit.tier2))
                          .join(Unit.courses)
                          .filter(Course.id == self.id)
                          .first())[0]

    def __repr__(self): # pragma: no cover
        return '<Course: {0.abbr} - {0.title} {0.program}>'.format(self)


whoosh_index(app, Area)
whoosh_index(app, Unit)
whoosh_index(app, Outcome)
whoosh_index(app, Program)
whoosh_index(app, Course)

