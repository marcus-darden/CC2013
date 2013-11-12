import json

from flask import abort, jsonify, redirect, render_template, request, url_for

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
    return redirect('/program/{program.id}'.format(program=program))


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
            for course in program.courses:
                db.session.delete(course)
            db.session.delete(program)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            # Nonexistant action
            abort(404)
    else:
        # No action provided, display program summary
        units = []
        for course in program.courses:
            units.extend(course.units)
        unit_ids = [unit.id for unit in units]

        # Calculate the core hours for the courses in this program
        if unit_ids:
            tier1, tier2 = db.session.query(db.func.sum(Unit.tier1).label('Tier1'),
                                            db.func.sum(Unit.tier2).label('Tier2')).filter(
                                                Unit.id.in_(unit_ids)).first()
        else:
            tier1, tier2 = 0, 0

        # All core hours
        tier1_total, tier2_total = db.session.query(db.func.sum(Unit.tier1).label('Tier1'),
                                                    db.func.sum(Unit.tier2).label('Tier2')).first()
        return render_template('program.html', program=program,
                               courses=list(program.courses),
                               tier1=tier1, tier1_total=tier1_total,
                               tier2=tier2, tier2_total=tier2_total)


# Course creation
@app.route('/program/<int:program_id>/new_course')
def new_course(program_id):
    program = Program.query.filter_by(id=program_id).first_or_404()
    return render_template('edit_course.html', program=program)


# Execute course modification
@app.route('/program/<int:program_id>/edit_course/<int:course_id>/', methods=['POST'])
@app.route('/program/<int:program_id>/add_course', methods=['POST'])
def modify_course(program_id, course_id=None):
    # Get form data
    title = request.form['course_title'].strip()
    abbr = request.form['course_abbr'].strip()
    description = request.form['course_description'].strip()

    # Modify the course
    if course_id:
        # Course exists, so update properties
        course = Course.query.filter_by(id=course_id).first_or_404()
        if course.program.id != program_id:
            abort(404)
        course.title = title
        course.abbr = abbr
        course.description = description
    else:
        # Create new course object and store in the database
        program = Program.query.filter_by(id=program_id).first_or_404()
        course = Course(program, title, abbr, description)
        db.session.add(course)
    db.session.commit()

    #flash('New entry was successfully posted')
    return redirect(url_for('course', program_id=program_id, course_id=course.id))


# Add Knowledge Units and/or Learning Outcomes to a course
@app.route('/program/<int:program_id>/course/<int:course_id>/add_<source>', methods=['POST'])
def add_outcomes(program_id, course_id, source):
    course = Course.query.filter_by(id=course_id).first_or_404()
    if course.program.id != program_id:
        abort(404)

    # Query outcomes selected on the page, by KU or individually
    if source == 'unit':
        units_list = request.form.getlist('knowledge_units')
        unit_ids = [int(unit) for unit in units_list]
        units = Unit.query.filter(Unit.id.in_(unit_ids)).all()
        outcomes = Outcome.query.filter(Outcome.unit_id.in_(unit_ids)).all()
    elif source == 'outcome':
        units = []
        outcomes_list = request.form.getlist('learning_outcomes')
        outcome_ids = [int(outcome) for outcome in outcomes_list]
        outcomes = Outcome.query.filter(Outcome.id.in_(outcome_ids)).all()
    else:
        abort(404)

    # Add the outcomes to the course and redisplay course information
    course.units.extend(units)
    #course.outcomes.extend(outcomes)
    db.session.commit()
    return redirect(url_for('course', program_id=program_id, course_id=course_id))


# Execute unit deletion
@app.route('/program/<int:program_id>/course/<int:course_id>/unit/<int:unit_id>/delete')
def delete_unit(program_id, course_id, unit_id):
    # Query db and verify that program_id, course_id, and unit_id are related
    course = Course.query.filter_by(id=course_id).first_or_404()
    if course.program.id != program_id:
        abort(404)
    unit = Unit.query.filter_by(id=unit_id).first_or_404()
    if unit not in course.units:
        abort(404)

    # Delete!
    #for outcome in unit.outcomes:
        #course.outcomes.remove(outcome)
    course.units.remove(unit)
    db.session.commit()

    return redirect(url_for('course', program_id=program_id, course_id=course_id))


# Execute outcome deletion
@app.route('/program/<int:program_id>/course/<int:course_id>/outcome/<int:outcome_id>/delete')
def delete_outcome(program_id, course_id, outcome_id):
    # Query db and verify that program_id, course_id, and outcome_id are related
    course = Course.query.filter_by(id=course_id).first_or_404()
    if course.program.id != program_id:
        abort(404)
    outcome = Outcome.query.filter_by(id=outcome_id).first_or_404()
    #if outcome not in course.outcomes:
        #abort(404)

    # Delete!
    #course.outcomes.remove(outcome)
    db.session.commit()

    return redirect(url_for('course', program_id=program_id, course_id=course_id))


# Course Information, and Course Edit/Delete
@app.route('/program/<int:program_id>/course/<int:course_id>/<action>')
@app.route('/program/<int:program_id>/course/<int:course_id>')
def course(program_id, course_id, action=None):
    course = Course.query.filter_by(id=course_id).first_or_404()
    if course.program.id != program_id:
        abort(404)

    if action:
        if action == 'edit':
            # Edit program level info
            return render_template('edit_course.html', course=course,
                                   program=course.program)
        elif action == 'delete':
            # Delete the given course
            # TODO: Add a confirmation dialog here
            db.session.delete(course)
            db.session.commit()
            return redirect(url_for('program', program_id=program_id))
        else:
            # Nonexistant action
            abort(404)
    else:
        # No action provided, display course information
        course_outcomes = (Outcome.query.join(Outcome.unit, Unit.courses)
                           .filter(Course.id == course_id)
                           .order_by(Outcome.tier, Outcome.id).all())
        areas = Area.query.order_by(Area.id).all()
        # TODO: Query for these numbers
        tier1 = sum([unit.tier1 for unit in course.units])
        tier2 = sum([unit.tier2 for unit in course.units])
        return render_template('course.html', course=course,
                               course_outcomes=course_outcomes, areas=areas,
                               tier1=tier1, tier2=tier2)


# AJAX here...
@app.route('/json')
def get_json():
    # Get form data...
    area_id = request.args.get('area_id', '')
    course_id = int(request.args.get('course_id', '0'))

    # Get listbox data
    if area_id:
        # A KA was selected, get all relevent KUs
        course = Course.query.filter_by(id=course_id).first()
        # TODO: Add join to these queries
        if course.units:
            units = Unit.query.filter_by(area_id=area_id).filter(~Unit.id.in_([u.id for u in course.units])).all()
        else:
            units = Unit.query.filter_by(area_id=area_id).all()
        junits = [{'id': u.id,
                   'text': u.text,
                   'tier1': u.tier1,
                   'tier2': u.tier2} for u in units]
        return json.dumps(junits)
    else:
        # A KU was selected, get all relevent LOs
        unit_id = request.args.get('unit_id', 0, type=int)
        outcomes = Outcome.query.filter_by(unit_id=unit_id).order_by(Outcome.number).all()
        joutcomes = [{'id': o.id,
                      'text': o.text,
                      'tier': o.tier,
                      'mastery': o.mastery} for o in outcomes]
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
        tier1 = Outcome.query.filter_by(tier='Tier 1').all()
        tier2 = Outcome.query.filter_by(tier='Tier 2').all()
        electives = Outcome.query.filter_by(tier='Elective').all()
        hours = None
    else:
        unit = Unit.query.filter_by(id=unit_id).first_or_404()
        if unit.area.id != area_id:
            abort(404)
        area = unit.area
        tier1 = Outcome.query.filter_by(unit_id=unit_id, tier='Tier 1').all()
        tier2 = Outcome.query.filter_by(unit_id=unit_id, tier='Tier 2').all()
        electives = Outcome.query.filter_by(unit_id=unit_id, tier='Elective').all()
        hours = db.session.query(db.func.sum(Unit.tier1).label('Tier1'),
                                 db.func.sum(Unit.tier2).label('Tier2')).filter(Unit.id == unit_id).first()

    return render_template('outcomes.html', **locals())


# Not found...
@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404
