from datetime import datetime
import json

from flask import abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.babel import gettext
from flask.ext.sqlalchemy import get_debug_queries

from config import DATABASE_QUERY_TIMEOUT, LANGUAGES, PROGRAMS_PER_PAGE, WHOOSH_ENABLED
from CC2013 import app, db, lm, oid, babel
from models import *
from forms import *


# OpenID Login
@app.route('/login',
           methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('user_profile', nickname=g.user.nickname))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])

    return render_template('login.html', form=form,
                           providers=app.config['OPENID_PROVIDERS'])


# Site logout
@app.route('/logout')
def logout():
    logout_user()

    return redirect(url_for('index'))


# User info page
@app.route('/user/<nickname>')
def user_profile(nickname):
    user = User.query.filter_by(nickname=nickname).first_or_404()

    return render_template('user.html', user=user)


# User Edit Details
@app.route('/user/settings',
           methods=['GET', 'POST'])
@login_required
def user_settings():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()

        return redirect(url_for('user_profile', nickname=g.user.nickname))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me

    return render_template('user_edit.html', form=form)


# Homepage
@app.route('/')
@app.route('/index')
@app.route('/index/<int:page>')
def index(page=1):
    return render_template('index.html', homepage=True,
                           form=LoginForm(),
                           providers=app.config['OPENID_PROVIDERS'],
                           programs=Program.query.paginate(page,
                                                           PROGRAMS_PER_PAGE,
                                                           False))


# Program creation
@app.route('/program/new',
           methods=['GET', 'POST'])
@login_required
def program_new():
    if request.method == 'GET':
        return render_template('program_edit_details.html')
    elif request.method == 'POST':
        """Execute program creation"""
        # Get data from form
        title = request.form['program_title'].strip()
        description = request.form['program_description'].strip()

        # Create new program object and store in the database
        program = Program(user=g.user, title=title, description=description)
        db.session.add(program)
        db.session.commit()

        return redirect(url_for('program', program_id=program.id))


# Program Edit Details
@app.route('/program/<int:program_id>/edit-details',
           methods=['GET', 'POST'])
@login_required
def program_edit_details(program_id):
    program = Program.query.get_or_404(program_id)
    if request.method == 'GET':
        if program.user_id != g.user.id:
            abort(403)

        return render_template('program_edit_details.html', program=program)
    elif request.method == 'POST':
        # Verify db access
        if program.user_id != g.user.id:
            abort(403)

        # Get form data and update program
        program.title = request.form['program_title'].strip()
        program.description = request.form['program_description'].strip()
        db.session.commit()

        return redirect(url_for('program', program_id=program_id))


# Program Summary
@app.route('/program/<int:program_id>')
def program(program_id):
    # Verify db access
    program = Program.query.get_or_404(program_id)

    return render_template('program.html', program=program)


@app.route('/program/<int:program_id>/delete',
           methods=['POST'])
@login_required
def program_delete(program_id):
    # Verify db access
    program = Program.query.get_or_404(program_id)
    if program.user.id != g.user.id:
        abort(403)

    db.session.delete(program)
    db.session.commit()

    return redirect(url_for('user_profile', nickname=g.user.nickname))


# Course creation
@app.route('/program/<int:program_id>/course/new',
           methods=['GET', 'POST'])
@login_required
def course_new(program_id):
    # Verify db access
    program = Program.query.get_or_404(program_id)
    if program.user_id != g.user.id:
        abort(403)

    if request.method == 'GET':
        return render_template('course_edit_details.html', program=program)
    elif request.method == 'POST':
        # Get form data
        title = request.form['course_title'].strip()
        abbr = request.form['course_abbr'].strip()
        description = request.form['course_description'].strip()
    
        # Create new course object and store in the database
        course = Course(program=program, title=title, abbr=abbr, description=description)
        db.session.add(course)
        db.session.commit()

        return redirect(url_for('course',
                                program_id=program_id,
                                course_id=course.id))


# Course Edit Details
@app.route('/program/<int:program_id>/course/<int:course_id>/edit-details',
           methods=['GET', 'POST'])
@login_required
def course_edit_details(program_id, course_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if course.program_id != program_id:
        abort(404)
    if course.program.user_id != g.user.id:
        abort(403)

    if request.method == 'GET':
        return render_template('course_edit_details.html',
                               program=course.program,
                               course=course) 
    elif request.method == 'POST':
        # Get form data and edit the course
        course.title = request.form['course_title'].strip()
        course.abbr = request.form['course_abbr'].strip()
        course.description = request.form['course_description'].strip()

        db.session.add(course)
        db.session.commit()

        return redirect(url_for('course',
                                program_id=program_id,
                                course_id=course.id))


# Course Information
@app.route('/program/<int:program_id>/course/<int:course_id>')
def course(program_id, course_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if course.program.id != program_id:
        abort(404)

    return render_template('course.html', course=course)


@app.route('/program/<int:program_id>/course/<int:course_id>/delete',
           methods=['POST'])
def course_delete(program_id, course_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if course.program.id != program_id:
        abort(404)
    if course.program.user.id != g.user.id:
        abort(403)

    db.session.delete(course)
    db.session.commit()

    return redirect(url_for('program', program_id=program_id))
    

# Add Knowledge Units to a course
@app.route('/program/<int:program_id>/course/<int:course_id>/edit-content')
@login_required
def course_edit_content(program_id, course_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if course.program.id != program_id:
        abort(404)
    if course.program.user_id != g.user.id:
        abort(403)

    return render_template('course_edit_content.html',
                           course=course,
                           areas=Area.query.all())


# Execute unit deletion
@app.route('/program/<int:program_id>/course/<int:course_id>/unit/<int:unit_id>/delete')
@login_required
def delete_unit(program_id, course_id, unit_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if (course.program.id != program_id
        or course.program.user_id != g.user.id):
        abort(404)
    unit = Unit.query.get_or_404(unit_id)
    if unit not in course.units:
        abort(404)

    # Delete!
    course = course.remove_unit(unit)
    db.session.add(course)
    db.session.commit()

    return redirect(url_for('course', program_id=program_id, course_id=course_id))


# AJAX here...
@app.route('/json/course_content')
def get_course_content():
    # Get request parameters
    course_id = request.args.get('course_id', 0, type=int)

    course = Course.query.get(course_id)
    units_json = [unit.json() for unit in course.units]

    return json.dumps(units_json)


@app.route('/json/unassigned_units')
def get_unassigned_units():
    # Get request parameters
    area_id = request.args.get('area_id', '')
    course_id = request.args.get('course_id', 0, type=int)

    # Query db
    program = Course.query.get(course_id).program
    units = program.get_unassigned_units(area_id)
    units_json = [unit.json() for unit in units]

    return json.dumps(units_json)


@app.route('/json/unit_area_id')
def get_unit_area_id():
    # Get request parameters
    unit_id = request.args.get('unit_id', 0, type=int)
    unit = Unit.query.get(unit_id)

    response = {'unit': unit.json(),
                'area': unit.area.json()}

    return json.dumps(response)


@app.route('/json/unit_outcomes')
def get_unit_outcomes():
    # Get request parameters
    unit_id = request.args.get('unit_id', 0)
    unit = Unit.query.get(unit_id)

    response = {'unit': unit.json(),
                'outcomes': [outcome.json() for outcome in unit.outcomes]}

    return json.dumps(response)


# General curriculum exemplar browser
# Browser: Knowledge Areas
@app.route('/areas')
def knowledge_areas():
    areas = Area.query.all()
    hours = (db.session.query(db.func.sum(Unit.tier1),
                              db.func.sum(Unit.tier2))
                       .group_by(Unit.area_id)
                       .order_by(Unit.area_id)
                       .all())

    return render_template('areas.html', areas=areas, hours=hours)


# Browser: Knowledge Units
@app.route('/units')
@app.route('/area/<area_id>')
def knowledge_units(area_id=None):
    if area_id:
        area = Area.query.get_or_404(area_id)
        units = area.units.all()
    else:
        area = None
        units = Unit.query.order_by(Unit.id).all()
    hours = [(db.session.query(db.func.sum(Unit.tier1),
                               db.func.sum(Unit.tier2))
                        .filter(Unit.id == unit.id)
                        .first())
             for unit in units]

    return render_template('units.html', area=area, units=units, hours=hours)


# Browser: Learning Outcomes
@app.route('/outcomes')
@app.route('/area/<area_id>/unit/<int:unit_id>')
def learning_outcomes(area_id=None, unit_id=-1):
    if unit_id < 0:
        tier1 = Outcome.query.filter_by(tier='Tier 1').all()
        tier2 = Outcome.query.filter_by(tier='Tier 2').all()
        electives = Outcome.query.filter_by(tier='Elective').all()
        hours = None
    else:
        unit = Unit.query.get_or_404(unit_id)
        if unit.area.id != area_id:
            abort(404)
        area = unit.area
        tier1 = Outcome.query.filter_by(unit_id=unit_id, tier='Tier 1').all()
        tier2 = Outcome.query.filter_by(unit_id=unit_id, tier='Tier 2').all()
        electives = Outcome.query.filter_by(unit_id=unit_id, tier='Elective').all()
        hours = (db.session.query(db.func.sum(Unit.tier1),
                                  db.func.sum(Unit.tier2))
                           .filter(Unit.id == unit_id)
                           .first())

    return render_template('outcomes.html', **locals())


# Login activities
# Load user
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


# Login callback
@oid.after_login
def after_login(response):
    if response.email is None or response.email == '':
        flash(gettext('Invalid login. Please try again.'))
        return redirect(url_for('login'))
    user = User.query.filter_by(email=response.email).first()
    if user is None:
        # Create a new user
        nickname = response.nickname
        if nickname is None or nickname == '':
            nickname = response.email.split('@')[0]
        nickname = User.make_unique_nickname(nickname)
        nickname = User.make_valid_nickname(nickname)
        user = User(nickname=nickname, email=response.email, role=ROLE_USER)
        db.session.add(user)
        db.session.commit()

    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
    g.locale = get_locale()
    g.search_enabled = WHOOSH_ENABLED


@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= DATABASE_QUERY_TIMEOUT:
            app.logger.warning('SLOW QUERY: {0.statement}\n'
                               'Parameters: {0.parameters}\n'
                               'Duration: {0.duration:f}s\n'
                               'Context: {0.context}\n'.format(query))

    return response


# Error Handling
# Not Found
@app.errorhandler(404)
def internal_error(error):
    return render_template('error.html', error=404), 404


# Other error
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error=500), 500


# Languages and i18n
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())
