import json

from flask import abort, redirect, render_template, request, url_for

from CC2013 import app
from CC2013.models import *


# Homepage
@app.route('/')
def index():
    programs = Program.query.order_by(Program.title).all()
    return render_template('programs.html', programs=programs)


# Program creation
@app.route('/new_program')
def new_program():
    return render_template('edit_program.html')


# Execute program modification
@app.route('/edit_program/<int:program_id>', methods=['POST'])
@app.route('/add_program', methods=['POST'])
def modify_program(program_id=None):
    title = request.form['program_title'].strip()
    description = request.form['program_description'].strip()

    # Query db if necessary
    if program_id:
        # Program exists, so update properties
        program = Program.query.filter_by(id=program_id).first_or_404()
        program.title = title
        program.description = description
    else:
        # Create new program object and store in the database
        program = Program(title, description)
        db.session.add(program)
    db.session.commit()

    #flash('New entry was successfully posted')
    return redirect('/program/{0}'.format(program.id))


# Program Summary, and Program Edit/Delete
@app.route('/program/<int:program_id>/<action>')
@app.route('/program/<int:program_id>')
def program(program_id, action=None):
    # Query db
    program = Program.query.filter_by(id=program_id).first_or_404()

    if action:
        if action == 'edit':
            # Edit program level info
            return render_template('edit_program.html', program=program)
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
        units = []
        for course in courses:
            units.extend(course.units)
        unit_ids = [unit.id for unit in units]
        print 'courses', courses
        print 'units', units
        print 'unit_ids', unit_ids

        if unit_ids:
            tier1, tier2 = db.session.query(db.func.sum(Unit.tier1).label('Tier1'),
                                            db.func.sum(Unit.tier2).label('Tier2')).filter(
                                                Unit.id.in_(unit_ids)).first()
        else:
            tier1, tier2 = 0, 0
        tier1_total, tier2_total = db.session.query(db.func.sum(Unit.tier1).label('Tier1'),
                                                    db.func.sum(Unit.tier2).label('Tier2')).first()
        return render_template('program.html', program=program, courses=courses,
                               tier1=tier1, tier2=tier2,
                               tier1_total=tier1_total,
                               tier2_total=tier2_total)


# Course creation
@app.route('/program/<int:program_id>/new_course')
def new_course(program_id):
    program = Program.query.filter_by(id=program_id).first_or_404()
    return render_template('edit_course.html', program=program)


# Execute course modification
@app.route('/program/<int:program_id>/edit_course/<int:course_id>/', methods=['POST'])
@app.route('/program/<int:program_id>/add_course', methods=['POST'])
def modify_course(program_id, course_id=None):
    title = request.form['course_title'].strip()
    abbr = request.form['course_abbr'].strip()
    description = request.form['course_description'].strip()

    # Query db
    program = Program.query.filter_by(id=program_id).first_or_404()
    if course_id:
        # Course exists, so update properties
        course = Course.query.filter_by(id=course_id).first_or_404()
        course.title = title
        course.abbr = abbr
        course.description = description
    else:
        # Create new course object and store in the database
        course = Course(program, title, abbr, description)
        db.session.add(course)
    db.session.commit()

    #flash('New entry was successfully posted')
    return redirect(url_for('course', program_id=program.id, course_id=course.id))


# Add Knowledge Units and/or Learning Outcomes to a course
@app.route('/program/<int:program_id>/course/<int:course_id>/add_<source>', methods=['POST'])
def add_outcomes(program_id, course_id, source):
    program = Program.query.filter_by(id=program_id).first_or_404()
    course = Course.query.filter_by(id=course_id).first_or_404()

    # Lookup outcomes selected on the page, in the database
    if source == 'unit':
        getlist = request.form.getlist('knowledge_units')
        unit_ids = [int(item) for item in getlist]
        units = Unit.query.filter(Unit.id.in_(unit_ids)).all()
        course.units.extend(units)
        outcomes = Outcome.query.filter(Outcome.unit_id.in_(unit_ids)).all()
    elif source == 'outcome':
        getlist = request.form.getlist('learning_outcomes')
        outcome_ids = [int(item) for item in getlist]
        outcomes = Outcome.query.filter(Outcome.id.in_(outcome_ids)).all()
    else:
        abort(404)

    # Add the outcomes to the course and redisplay course information
    course.outcomes.extend(outcomes)
    db.session.commit()
    return redirect(url_for('course', program_id=program_id, course_id=course_id))


# Execute unit deletion
@app.route('/program/<int:program_id>/course/<int:course_id>/unit/<int:unit_id>/delete')
def delete_unit(program_id, course_id, unit_id):
    # TODO: Verify that program_id, course_id, and unit_id are related
    course = Course.query.filter_by(id=course_id).first_or_404()
    if course.program.id != program_id:
        abort(404)
    unit = Unit.query.filter_by(id=unit_id).first_or_404()
    if unit in course.units:
        course.units.remove(unit)
        db.session.commit()
    else:
        abort(404)
    return redirect(url_for('course', program_id=program_id, course_id=course_id))


# Execute outcome deletion
@app.route('/program/<int:program_id>/course/<int:course_id>/outcome/<int:outcome_id>/delete')
def delete_outcome(program_id, course_id, outcome_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    outcome = Outcome.query.filter_by(id=outcome_id).first_or_404()
    course.outcomes.remove(outcome)
    db.session.commit()
    return redirect(url_for('course', program_id=program_id, course_id=course_id))


# Course Information, and Course Edit/Delete
@app.route('/program/<int:program_id>/course/<int:course_id>/<action>')
@app.route('/program/<int:program_id>/course/<int:course_id>')
def course(program_id, course_id, action=None):
    program = Program.query.filter_by(id=program_id).first_or_404()
    course = Course.query.filter_by(id=course_id).first_or_404()

    if action:
        if action == 'edit':
            # Edit program level info
            return render_template('edit_course.html', program=program, course=course)
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
        t1 = [outcome for outcome in course.outcomes if outcome.tier == 1]
        t2 = [outcome for outcome in course.outcomes if outcome.tier == 2]
        elec = [outcome for outcome in course.outcomes if outcome.tier == 3]
        course_outcomes = [t1, t2, elec]
        areas = Area.query.order_by(Area.id).all()
        tier1 = sum([unit.tier1 for unit in course.units])
        tier2 = sum([unit.tier2 for unit in course.units])
        return render_template('course.html', program=program, course=course,
                               course_outcomes=course_outcomes, areas=areas,
                               tier1=tier1, tier2=tier2)


# AJAX here...
@app.route('/json')
def get_json():
    area_id = request.args.get('area_id', '')
    course_id = int(request.args.get('course_id', '0'))
    if area_id:
        course = Course.query.filter_by(id=course_id).first()
        print course
        if course.units:
            units = Unit.query.filter_by(area_id=area_id).filter(~Unit.id.in_([u.id for u in course.units])).all()
        else:
            units = Unit.query.filter_by(area_id=area_id).all()
        junits = [{'id': u.id, 'text': u.text, 'tier1': u.tier1, 'tier2': u.tier2} for u in units]
        return json.dumps(junits)
    else:
        unit_id = request.args.get('unit_id', 0, type=int)
        outcomes = Outcome.query.filter_by(unit_id=unit_id).order_by(Outcome.number).all()
        joutcomes = [{'id': o.id, 'text': o.text, 'tier': ['', 'Tier 1', 'Tier 2', 'Elective'][o.tier], 'mastery': o.mastery} for o in outcomes]
        return json.dumps(joutcomes)


# General curriculum exemplar browser
@app.route('/areas')
def knowledge_areas():
    areas = Area.query.all()
    hours = [db.session.query(db.func.sum(Unit.tier1).label('Tier1'),
                              db.func.sum(Unit.tier2).label('Tier2')).filter(Unit.area_id == area.id).first() for area in areas]
    return render_template('areas.html', areas=areas, hours=hours)


@app.route('/units')
@app.route('/area/<area_id>')
def knowledge_units(area_id=None):
    if not area_id:
        area = None
        units = Unit.query.order_by(Unit.id).all()
    else:
        area = Area.query.filter_by(id=area_id).first_or_404()
        units = Unit.query.filter_by(area=area).all()
    hours = [db.session.query(db.func.sum(Unit.tier1).label('Tier1'),
                              db.func.sum(Unit.tier2).label('Tier2')).filter(Unit.id == unit.id).first() for unit in units]

    return render_template('units.html', area=area, units=units, hours=hours)


@app.route('/outcomes')
@app.route('/area/<area_id>/unit/<int:unit_id>')
def learning_outcomes(area_id=None, unit_id=-1):
    if unit_id < 0:
        tier1 = Outcome.query.filter_by(tier=1).all()
        tier2 = Outcome.query.filter_by(tier=2).all()
        electives = Outcome.query.filter_by(tier=3).all()
        hours = None
    else:
        unit = Unit.query.filter_by(id=unit_id).first_or_404()
        if unit.area.id != area_id:
            abort(404)
        area = unit.area
        tier1 = Outcome.query.filter_by(unit_id=unit_id, tier=1).all()
        tier2 = Outcome.query.filter_by(unit_id=unit_id, tier=2).all()
        electives = Outcome.query.filter_by(unit_id=unit_id, tier=3).all()
        hours = db.session.query(db.func.sum(Unit.tier1).label('Tier1'),
                                 db.func.sum(Unit.tier2).label('Tier2')).filter(Unit.id == unit_id).first()

    return render_template('outcomes.html', **locals())


# Not found...
@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404
