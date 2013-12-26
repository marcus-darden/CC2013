#!/usr/bin/env python

import os
import unittest

from coverage import coverage


cov = coverage(branch=True, omit=['/Users/ontoral/.virtualenvs/Fe/*', 'tests.py'])
cov.start()


from config import basedir
from CC2013 import app, db
from CC2013.models import *


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        db_filename = os.path.join(basedir, 'test.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_filename
        self.app = app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # Models
    # Unit
    def test_unit_model(self):
        u = Unit(text='Test Unit', tier1=1, tier2=0)
        db.session.add(u)
        db.session.commit()
        assert u.json() == {'id': 1,
                            'text': 'Test Unit',
                            'tier1': 1,
                            'tier2': 0}

    # Outcome
    def test_outcome_model(self):
        o = Outcome(text='Test Outcome', tier='Tier 1', mastery='Familiarity')
        db.session.add(o)
        db.session.commit()
        assert o.json() == {'id': 1,
                            'text': 'Test Outcome',
                            'tier': 'Tier 1',
                            'mastery': 'Familiarity'}

    # User
    def test_avatar(self):
        u = User(nickname='john', email='john@example.com')
        avatar = u.avatar(128)
        expected = 'http://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6'
        assert avatar[0:len(expected)] == expected

    def test_make_unique_nickname(self):
        u = User(nickname='john', email='john@example.com')
        db.session.add(u)
        db.session.commit()
        nickname = User.make_unique_nickname('john')
        assert nickname != 'john'
        u = User(nickname=nickname, email='susan@example.com')
        db.session.add(u)
        db.session.commit()
        nickname2 = User.make_unique_nickname('john')
        assert nickname2 != 'john'
        assert nickname2 != nickname
        nickname3 = User.make_unique_nickname('isaiah')
        assert nickname3 == 'isaiah'

    def test_delete_course(self):
        # create a user, program, and course
        u = User(nickname='john', email='john@example.com')
        p = Program(user=u, title='Test Program', description='Testing 1, 2, 3...')
        c = Course(program=p, title='Test Course', abbr='101', description='Pass or Fail')
        db.session.add(u)
        db.session.add(p)
        db.session.add(c)
        db.session.commit()
        # query the post and destroy the session
        c = Course.query.get(1)
        db.session.remove()
        # delete the post using a new session
        db.session = db.create_scoped_session()
        db.session.delete(c)
        db.session.commit()

    def test_user(self):
        # make valid nicknames
        n = User.make_valid_nickname('John_123')
        assert n == 'John_123'
        n = User.make_valid_nickname('John_[123]\n')
        assert n == 'John_123'
        # create a user
        u = User(nickname='john', email='john@example.com')
        db.session.add(u)
        db.session.commit()
        assert u.is_authenticated() == True
        assert u.is_active() == True
        assert u.is_anonymous() == False
        assert u.id == int(u.get_id())

    def test_user_program(self):
        # create a user and program
        u = User(nickname='john', email='john@example.com')
        p = Program(title='Test Program', description='Testing 1, 2, 3...')
        db.session.add(u)
        db.session.add(p)
        db.session.commit()
        assert u.has_program(p) == False
        assert u.remove_program(p) is None
        assert u.add_program(p) is u
        db.session.commit()
        assert u.add_program(p) is None
        assert u.has_program(p) == True
        assert u.remove_program(p) is u

    # Program
    def test_program_course(self):
        # create a user, program, and course
        u = User(nickname='john', email='john@example.com')
        p = Program(user=u, title='Test Program', description='Testing 1, 2, 3...')
        c = Course(title='Test Course', abbr='101', description='Pass or Fail')
        db.session.add(u)
        db.session.add(p)
        db.session.add(c)
        db.session.commit()
        assert p.has_course(c) == False
        assert p.remove_course(c) is None
        assert p.add_course(c) is p
        db.session.commit()
        assert p.add_course(c) is None
        assert p.has_course(c) == True
        assert p.remove_course(c) is p

    def test_program(self):
        p = Program(title='Test Program', description='Major')
        c = Course(program=p, title='Test Course', abbr='101', description='Pass or Fail?')
        u = Unit(text='Test Unit', tier1=1, tier2=2)
        db.session.add(p)
        db.session.add(c)
        db.session.add(u)
        db.session.commit()
        assert len(c.outcomes) == 0
        assert c.has_unit(u) == False
        assert c.remove_unit(u) is None
        assert c.tier1_hours == 0
        assert c.tier2_hours == 0
        assert c.add_unit(u) is c
        db.session.commit()
        assert c.add_unit(u) is None
        assert c.has_unit(u) == True
        units = Unit.query.all()
        assert Program.all_tier1_hours() == 1
        assert Program.all_tier2_hours() == 2
        assert p.tier1_hours == 1
        assert p.tier2_hours == 2
        assert u not in p.get_unassigned_units(area_id='AREA').all()
        assert c.tier1_hours == 1
        assert c.tier2_hours == 2
        o = Outcome(unit=u, text='Test Outcome', tier='Tier 1', mastery='Familiarity')
        db.session.add(o)
        db.session.commit()
        assert c.outcomes == [o]
        assert c.remove_unit(u) is c
        u = Unit(text='Test Unit2', tier1=0, tier2=1)
        db.session.add(u)
        db.session.commit()
        assert u in p.get_unassigned_units().all()

    # momentjs
    def test_momentjs(self):
        from CC2013.momentjs import momentjs
        from datetime import datetime
        m = momentjs(datetime(2011, 5, 29, 15))
        test_str = 'moment("2011-05-29T15:00:00 Z")'
        assert test_str + '.format("L")' in m.format('L')
        assert test_str + '.calendar()' in m.calendar()
        assert test_str + '.fromNow()' in m.fromNow()


if __name__ == '__main__':
    try:
        unittest.main()
    except:
        pass
    cov.stop()
    cov.save()
    print '\n\nCoverage Report:\n'
    cov.report()
    print 'HTML version: {}'.format(os.path.join(basedir, 'tmp/coverage/index.html'))
    cov.html_report(directory='tmp/coverage')
    cov.erase()
