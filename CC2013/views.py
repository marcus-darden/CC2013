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
        return redirect(url_for('user', nickname=g.user.nickname))
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
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first_or_404()

    return render_template('user.html', user=user)


# User Edit Details
@app.route('/user/details',
           methods=['GET', 'POST'])
@login_required
def user_details():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()

        return redirect(url_for('user', nickname=g.user.nickname))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me

    return render_template('user_details.html', form=form)


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
        return render_template('program_details.html')
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
@app.route('/program/<int:program_id>/details',
           methods=['GET', 'POST'])
@login_required
def program_details(program_id):
    program = Program.query.get_or_404(program_id)
    if request.method == 'GET':
        if program.user_id != g.user.id:
            abort(403)

        return render_template('program_details.html', program=program)
    elif request.method == 'POST':
        # Verify db access
        if program.user_id != g.user.id:
            abort(403)

        # Get form data and update program
        program.title = request.form['program_title'].strip()
        program.description = request.form['program_description'].strip()
        db.session.add(program)
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

    return redirect(url_for('user', nickname=g.user.nickname))


# Course creation
@app.route('/program/<int:program_id>/course/new',
           methods=['GET', 'POST'])
@login_required
def course_new(program_id):
    # Verify db access
    print 'Querying for program...',
    program = Program.query.get_or_404(program_id)
    if program.user_id != g.user.id:
        abort(403)
    print program

    if request.method == 'GET':
        return render_template('course_details.html', program=program)
    elif request.method == 'POST':
        print 'METHOD: POST'
        # Get form data
        title = request.form['course_title'].strip()
        abbr = request.form['course_abbr'].strip()
        description = request.form['course_description'].strip()
    
        print 'form data:', title, abbr, description
        # Create new course object and store in the database
        course = Course(program=program, title=title, abbr=abbr, description=description)
        print 'course created:', course
        db.session.add(course)
        print 'course added'
        db.session.commit()
        print 'session committed'

        return redirect(url_for('course',
                                program_id=program_id,
                                course_id=course.id))


# Course Edit Details
@app.route('/program/<int:program_id>/course/<int:course_id>/details',
           methods=['GET', 'POST'])
@login_required
def course_details(program_id, course_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if course.program_id != program_id:
        abort(404)
    if course.program.user_id != g.user.id:
        abort(403)

    if request.method == 'GET':
        return render_template('course_details.html', course=course) 
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
    

# Modify the Knowledge Units in a Course
@app.route('/program/<int:program_id>/course/<int:course_id>/content',
           methods=['GET', 'POST'])
@login_required
def course_content(program_id, course_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if course.program.id != program_id:
        abort(404)
    if course.program.user_id != g.user.id:
        abort(403)

    if request.method == 'GET':
        return render_template('course_content.html',
                               course=course,
                               areas=Area.query.all())
    elif request.method == 'POST':
        # Get request parameters
        add = json.loads(request.form['add'])
        unit_ids = json.loads(request.form['units'])
        units = Unit.query.filter(Unit.id.in_(unit_ids)).all()

        # Add/Remove the units
        if add:
            for unit in units:
                course = course.add_unit(unit)
        else:
            for unit in units:
                course = course.remove_unit(unit)

        db.session.add(course)
        db.session.commit()

        return json.dumps(True)


# AJAX here...
@app.route('/program/<int:program_id>/course/<int:course_id>/units')
def course_units(program_id, course_id):
    # Get request parameters
    course = Course.query.get(course_id)
    units_json = [unit.json() for unit in course.units]

    return json.dumps(units_json)


@app.route('/program/<int:program_id>/unassigned')
def unassigned_units(program_id):
    # Get request parameters
    area_id = request.args.get('area_id', '')

    # Query db
    program = Program.query.get_or_404(program_id)
    units = program.get_unassigned_units(area_id)
    units_json = [unit.json() for unit in units]

    return json.dumps(units_json)


@app.route('/program/<int:program_id>/coverage')
def program_coverage(program_id):
    program = Program.query.get_or_404(program_id)
    if not len(program.courses.all()):
        return ''
    titles, tier1_hours, tier2_hours = program.content_coverage()

    # Highcharts.com data structure
    # Draws a stacked bar graph
    #
    #  Course 1   |  +++++++++oooooo
    #  Course 2   |  +++oooooooo
    #             -------------------
    #             0  1  2  3  4  5  6 
    #
    #       o: Tier 1 Hours, +: Tier 2 Hours
    chart_json = {
        'chart': {'type': 'bar'},
        'title': {'text': 'Core Content by Course'},
        'xAxis': {
            'title': {'text': None},
            'categories': titles
        },
        'yAxis': {'title': {'text': None}},
        'plotOptions': {'series': {'stacking': 'normal'}},
        'series': [{
            'type': 'column',
            'name': 'Tier 1 Hours',
            'data': tier1_hours
        }, {
            'type': 'column',
            'name': 'Tier 2 Hours',
            'data': tier2_hours
        }]
    }

    return json.dumps(chart_json)


@app.route('/unit/<int:unit_id>/outcomes')
def unit_outcomes(unit_id):
    # Get request parameters
    unit = Unit.query.get(unit_id)

    response = {'unit': unit.json(),
                'outcomes': [outcome.json() for outcome in unit.outcomes]}

    return json.dumps(response)


# General curriculum exemplar browser
# Browser: Knowledge Areas
@app.route('/area')
def knowledge_areas():
    areas = Area.query.all()
    hours = (db.session.query(db.func.sum(Unit.tier1),
                              db.func.sum(Unit.tier2))
                       .group_by(Unit.area_id)
                       .order_by(Unit.area_id)
                       .all())

    return render_template('areas.html', areas=areas, hours=hours)


# Browser: Knowledge Units
@app.route('/area/<area_id>/unit')
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
@app.route('/area/<area_id>/unit/<int:unit_id>/outcome')
def learning_outcomes(area_id=None, unit_id=0):
    if unit_id:
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
    else:
        tier1 = Outcome.query.filter_by(tier='Tier 1').all()
        tier2 = Outcome.query.filter_by(tier='Tier 2').all()
        electives = Outcome.query.filter_by(tier='Elective').all()
        hours = None

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
    #if g.user.is_authenticated():
        #g.user.last_seen = datetime.utcnow()
        #db.session.add(g.user)
        #db.session.commit()
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
