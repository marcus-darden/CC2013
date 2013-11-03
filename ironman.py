#!/usr/bin/env python

'''Web front end for Computing Curricula 2013 Curriculum Exemplar (Ironman version).

Preconditions:
    environment - python 2 >= 2.7.3, flask, flask-sqlalchemy, gunicorn
'''
import csv

from flask import Flask, abort, redirect, render_template, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'Computing Curricula 2013'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
db = SQLAlchemy(app)


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
    area_id = db.Column(db.String, db.ForeignKey('area.id'))
    outcomes = db.relationship('Outcome', backref='unit', lazy='dynamic')

    def __init__(self, area, text, tier1, tier2):
        self.area_id = area.id
        self.text = text.strip()
        self.tier1 = tier1
        self.tier2 = tier2

    def __str__(self):
        return '<KA: {0.area} Knowledge Unit: "{0.text}" Hours: ({0.tier1}, {0.tier2})>'.format(self)


class Outcome(db.Model):
    '''A "Learning Outcome", as defined in CC2013.'''
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(256))
    tier = db.Column(db.Integer)
    mastery = db.Column(db.Enum('Familiarity', 'Usage', 'Assessment', name='outcome_mastery'))
    number = db.Column(db.Integer)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))

    def __init__(self, unit, tier, mastery, number, text):
        self.unit_id = unit.id
        self.tier = tier
        self.mastery = mastery
        self.number = number
        self.text = text.strip()

    def __repr__(self):
        #return str(self.__dict__)
        return '<Outcome: {0.number:2d}. {0.text} Tier: {0.tier} Mastery: {0.mastery} {0.unit}>'.format(self)


class Program(db.Model):
    '''A collection of courses built to cover "Learning Outcomes".'''
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), unique=True)
    description = db.Column(db.String)
    courses = db.relationship('Course', backref='program', lazy='dynamic')

    def __init__(self, title=None, description=None):
        self.title = title
        self.description = description

    def __repr__(self):
        return '<Program: {0.title}>'.format(self)


class Course(db.Model):
    '''A member of a program built to cover "Learning Outcomes".'''
    id = db.Column(db.Integer, primary_key=True)
    abbr = db.Column(db.String(8))
    title = db.Column(db.String(128))
    description = db.Column(db.String)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))

    def __init__(self, program, title, abbr=None, description=None):
        self.program_id = program.id
        self.title = title
        self.abbr = abbr
        self.description = description

    def __repr__(self):
        return '<Course: {0.abbr} - {0.title} {0.program}>'.format(self)


# Initialize the database
@app.before_first_request
def init_db():
    db.create_all()

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

                tier = int(row[2])
                mastery = row[3].strip()
                number = int(row[4])
                text = row[5].strip()
                outcome = Outcome(unit, tier, mastery, number, text)
                db.session.add(outcome)
                #print outcome
    db.session.commit()


@app.route('/')
@app.route('/programs')
def index():
    programs = Program.query.order_by(Program.title).all()
    return render_template('programs.html', programs=programs)


@app.route('/program')
@app.route('/new_program')
def new_program():
    return render_template('new_program.html')


@app.route('/edit_program/<int:program_id>', methods=['POST'])
@app.route('/add_program', methods=['POST'])
def modify_program(program_id=None):
    title = request.form['title'].strip()
    description = request.form['description'].strip()

    # Query db if necessary
    if program_id:
        # Program exists, so update properties
        program = Program.query.filter_by(id=program_id).first_or_404()
        if not title:
            return render_template('new_program.html', program=program,
                                   message='Required field(s) cannot be left blank.')
        program.title = title
        program.description = description
    else:
        # Create new program object and store in the database
        if not title:
            return render_template('new_program.html', description=description,
                                   message='Required field(s) cannot be left blank.')
        program = Program(title, description)
        db.session.add(program)
    db.session.commit()

    #flash('New entry was successfully posted')
    return redirect('/program/{0}'.format(program.id))


@app.route('/program/<int:program_id>/<action>')
@app.route('/program/<int:program_id>')
def program(program_id, action=None):
    # Query db
    program = Program.query.filter_by(id=program_id).first_or_404()

    if action:
        if action == 'edit':
            # Edit program level info
            return render_template('new_program.html', program=program)
        elif action == 'delete':
            # Delete the given program
            # TODO: Add a confirmation dialog here
            courses = Course.query.filter_by(program_id=program.id).all()
            for course in courses:
                db.session.delete(course)
            db.session.delete(program)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            # Nonexistant action
            abort(404)
    else:
        # No action provided, display program summary
        courses = Course.query.filter_by(program_id=program_id).all()
        return render_template('program.html', program=program, courses=courses)


@app.route('/program/<int:program_id>/new_course')
def new_course(program_id):
    program = Program.query.filter_by(id=program_id).first_or_404()
    return render_template('new_course.html', program=program)


@app.route('/program/<int:program_id>/edit_course/<int:course_id>/', methods=['POST'])
@app.route('/program/<int:program_id>/add_course', methods=['POST'])
def modify_course(program_id, course_id=None):
    title = request.form['title'].strip()
    abbr = request.form['abbr'].strip()
    description = request.form['description'].strip()

    # Query db
    program = Program.query.filter_by(id=program_id).first_or_404()
    if course_id:
        # Course exists, so update properties
        course = Course.query.filter_by(program_id=program_id).first_or_404()
        if not title:
            return render_template('new_course.html',
                                   program=program, course=course,
                                   message='Required field(s) cannot be left blank.')
        course.title = title
        course.abbr = abbr
        course.description = description
    else:
        # Create new course object and store in the database
        if not title:
            return render_template('new_course.html', program=program,
                                   abbr=abbr, description=description,
                                   message='Required field(s) cannot be left blank.')
        course = Course(program, title, abbr, description)
        db.session.add(course)
    db.session.commit()

    #flash('New entry was successfully posted')
    return redirect(url_for('course', program_id=program.id, course_id=course.id))


@app.route('/program/<int:program_id>/course/<int:course_id>/<action>')
@app.route('/program/<int:program_id>/course/<int:course_id>')
def course(program_id, course_id, action=None):
    program = Program.query.filter_by(id=program_id).first_or_404()
    course = Course.query.filter_by(id=course_id).first_or_404()

    if action:
        if action == 'edit':
            # Edit program level info
            return render_template('new_course.html', program=program, course=course)
        elif action == 'delete':
            # Delete the given course
            # TODO: Add a confirmation dialog here
            db.session.delete(course)
            db.session.commit()
            return redirect(url_for('program', program_id=program.id))
        else:
            # Nonexistant action
            abort(404)
    else:
        # No action provided, display course information
        course_outcomes = [['Tier 1 sample'], ['Tier 2 sample'], ['Elective sample']]
        areas = Area.query.order_by(Area.id).all()
        #units = Unit.query.filter_by(area_id='AL').order_by(Unit.id).all()
        #outcomes = Outcome.query.filter_by(unit_id=units[0].id).order_by(Outcome.number).all()
        return render_template('course.html', program=program, course=course,
                               course_outcomes=course_outcomes, areas=areas)
                               #units=units, outcomes=outcomes)


@app.route('/areas')
def knowledge_areas():
    areas = Area.query.all()
    return render_template('areas.html', areas=areas)


@app.route('/units/<area_id>')
def knowledge_units(area_id):
    area = Area.query.filter_by(id=area_id).first()
    units = Unit.query.filter_by(area=area).all()
    return render_template('units.html', area=area, units=units)


@app.route('/outcomes/<int:unit_id>')
@app.route('/outcomes')
def learning_outcomes(unit_id=-1):
    if unit_id < 0:
        tier1 = Outcome.query.filter_by(tier=1).all()
        tier2 = Outcome.query.filter_by(tier=2).all()
        electives = Outcome.query.filter_by(tier=3).all()
    else:
        unit = Unit.query.filter_by(id=unit_id).first()
        area = unit.area
        tier1 = Outcome.query.filter_by(unit_id=unit_id, tier=1).all()
        tier2 = Outcome.query.filter_by(unit_id=unit_id, tier=2).all()
        electives = Outcome.query.filter_by(unit_id=unit_id, tier=3).all()

    return render_template('outcomes.html', **locals())


@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404


if __name__ == '__main__':
    app.run()
