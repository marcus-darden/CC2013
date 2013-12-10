from datetime import datetime
import json

from flask import abort, jsonify, g, redirect, render_template, request, session, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required

from CC2013 import app, db, lm, oid
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
    user = User.query.filter_by(nickname=nickname).first()
    if not user:
        #flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    programs = user.programs.all()

    return render_template('user.html', user=user, programs=programs)


# Edit user information
@app.route('/user/settings', methods = ['GET', 'POST'])
@login_required
def user_settings():
    form = EditForm()
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        #flash('Your changes have been saved.')
        return redirect(url_for('user_profile', nickname=g.user.nickname))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me

    return render_template('edit_user.html', form=form)


# Homepage
@app.route('/')
def index():
    return render_template('index.html', form=LoginForm(),
                           providers=app.config['OPENID_PROVIDERS'],
                           programs=Program.query.all())


# Program creation
@app.route('/program/new')
@login_required
def program_new():
    return render_template('edit_program.html')


@app.route('/program/new',
           methods=['POST'])
@login_required
def program_new_post():
    """Execute program creation"""
    # Get data from form
    title = request.form['program_title'].strip()
    description = request.form['program_description'].strip()

    # Create new program object and store in the database
    program = Program(g.user, title, description)
    db.session.add(program)
    db.session.commit()

    #flash('New entry was successfully posted')
    return redirect(url_for('program', program_id=program.id))


@app.route('/program/<int:program_id>/edit')
@login_required
def program_edit(program_id):
    program = Program.query.get_or_404(program_id)
    if program.user_id != g.user.id:
        abort(403)

    return render_template('edit_program.html', program=program)


# Execute program edit
@app.route('/program/<int:program_id>/edit',
           methods=['POST'])
@login_required
def program_edit_post(program_id):
    # Verify db access
    program = Program.query.get_or_404(program_id)
    if program.user_id != g.user.id:
        abort(403)

    # Get form data and update program
    program.title = request.form['program_title'].strip()
    program.description = request.form['program_description'].strip()
    db.session.commit()

    #flash('New entry was successfully posted')
    return redirect(url_for('program', program_id=program_id))


# Program Summary
@app.route('/program/<int:program_id>')
def program(program_id):
    # Query db
    program = Program.query.get_or_404(program_id)

    # Calculate the core hours for the courses in this program
    subquery = (Unit.query
                    .join(Unit.courses, Course.program)
                    .filter(Program.id == 1)
                    .subquery())
    tier1, tier2 = (db.session.query(db.func.sum(subquery.c.tier1),
                                     db.func.sum(subquery.c.tier2))
                              .first())

    # All core hours
    tier1_total, tier2_total = (db.session.query(db.func.sum(Unit.tier1),
                                                 db.func.sum(Unit.tier2))
                                          .first())

    return render_template('program.html', program=program,
                           courses=program.courses.all(),
                           tier1=tier1, tier1_total=tier1_total,
                           tier2=tier2, tier2_total=tier2_total)


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
@app.route('/program/<int:program_id>/course/new', methods=['GET'])
@login_required
def course_new(program_id):
    program = Program.query.get_or_404(program_id)
    if program.user_id != g.user.id:
        abort(403)

    return render_template('edit_course.html', program=program)


@app.route('/program/<int:program_id>/course/new',
           methods=['POST'])
@login_required
def course_new_post(program_id):
    # Verify db access
    program = Program.query.get_or_404(program_id)
    if program.user_id != g.user.id:
        abort(403)
    
    # Get form data
    title = request.form['course_title'].strip()
    abbr = request.form['course_abbr'].strip()
    description = request.form['course_description'].strip()
    
    # Create new course object and store in the database
    course = Course(program, title, abbr, description)
    db.session.add(course)
    db.session.commit()

    #flash('New entry was successfully posted')
    return redirect(url_for('course',
                            program_id=program_id,
                            course_id=course.id))


# Execute course modification
@app.route('/program/<int:program_id>/course/<int:course_id>/edit',
           methods=['GET'])
@login_required
def course_edit(program_id, course_id):
    course = Course.query.get_or_404(course_id)
    if course.program_id != program_id:
        abort(404)
    if course.program.user_id != g.user.id:
        abort(403)
    
    return render_template('edit_course.html',
                           program=course.program,
                           course=course) 


@app.route('/program/<int:program_id>/course/<int:course_id>/edit',
           methods=['POST'])
@login_required
def course_edit_post(program_id, course_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if course.program_id != program_id:
        abort(404)
    if course.program.user_id != g.user.id:
        abort(403)

    # Get form data and edit the course
    course.title = request.form['course_title'].strip()
    course.abbr = request.form['course_abbr'].strip()
    course.description = request.form['course_description'].strip()
    db.session.commit()

    #flash('New entry was successfully posted')
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

    areas = Area.query.order_by(Area.id).all()
    course_outcomes = (Outcome.query.join(Outcome.unit, Unit.courses)
                              .filter(Course.id == course_id)
                              .order_by(Outcome.tier, Outcome.id)
                              .all())
    tier1, tier2 = (db.session.query(db.func.sum(Unit.tier1),
                                     db.func.sum(Unit.tier2))
                              .join(Unit.courses)
                              .filter(Course.id == course_id)
                              .first())

    return render_template('course.html', course=course,
                           areas=areas, course_outcomes=course_outcomes,
                           tier1=tier1, tier2=tier2)


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
@app.route('/program/<int:program_id>/course/<int:course_id>/unit/add',
           methods=['POST'])
@login_required
def add_outcomes(program_id, course_id):
    # Verify db access
    course = Course.query.get_or_404(course_id)
    if course.program.id != program_id:
        abort(404)
    if course.program.user_id != g.user.id:
        abort(403)

    # Get form data and modify course
    units_list = request.form.getlist('knowledge_units')
    unit_ids = [int(unit) for unit in units_list]
    units = Unit.query.filter(Unit.id.in_(unit_ids)).all()
    outcomes = (Outcome.query
                       .filter(Outcome.unit_id.in_(unit_ids))
                       .all())
    course.units.extend(units)
    db.session.commit()

    return redirect(url_for('course',
                            program_id=program_id,
                            course_id=course_id))


# Execute unit deletion
@app.route('/program/<int:program_id>/course/<int:course_id>/unit/<int:unit_id>/delete')
@login_required
def delete_unit(program_id, course_id, unit_id):
    # Query db and verify that program_id, course_id, and unit_id are related
    course = Course.query.get_or_404(course_id)
    if (course.program.id != program_id
        or course.program.user_id != g.user.id):
        abort(404)
    unit = Unit.query.get_or_404(unit_id)
    if unit not in course.units:
        abort(404)

    # Delete!
    course.units.remove(unit)
    db.session.commit()

    return redirect(url_for('course', program_id=program_id, course_id=course_id))


# AJAX here...
@app.route('/json')
def get_json():
    # Get form data...
    area_id = request.args.get('area_id', '')
    course_id = int(request.args.get('course_id', '0'))

    # Get listbox data
    if area_id:
        # A KA was selected, get all relevent KUs, not assigned to this course
        course = Course.query.get(course_id)
        unwanted = (Unit.query
                        .filter_by(area_id=area_id)
                        .join(Unit.courses)
                        .filter_by(id=course_id)
                        .subquery())
        units = (Unit.query
                     .filter_by(area_id=area_id)
                     .outerjoin(unwanted, Unit.id == unwanted.c.id)
                     .filter(unwanted.c.id == None)
                     .all())
        items = [{'id': u.id,
                  'text': u.text,
                  'tier1': u.tier1,
                  'tier2': u.tier2} for u in units]
    else:
        # A KU was selected, get all relevent LOs
        unit_id = request.args.get('unit_id', 0, type=int)
        outcomes = (Outcome.query
                           .filter_by(unit_id=unit_id)
                           .order_by(Outcome.number)
                           .all())
        items = [{'id': o.id,
                  'text': o.text,
                  'tier': o.tier,
                  'mastery': o.mastery} for o in outcomes]

    return json.dumps(items)


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
        #flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=response.email).first()
    if user is None:
        # Create a new user
        nickname = response.nickname
        if nickname is None or nickname == '':
            nickname = response.email.split('@')[0]
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


# Error Handling
# Not Found
@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404
