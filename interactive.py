from CC2013 import app, db, oid, lm
from CC2013.models import *


# First user and first program
u = None
p = None

if User.query.count():
    u = User.query.get(1)
    if Program.query.count():
        p = Program.query.get(1)

# Create a user if none exists
if u is None:
    u = User()
    u.nickname = 'Ontoral'
    u.email = 'ontoral@gmail.com'
    db.session.add(u)
    db.session.commit()

# Create a program if none exists
if p is None:
    p = Program(user=u, title='CS Major [2014]', description='The Computer Science Major')
    db.session.add(p)
    db.session.commit()

    # Add some courses to the program
    cs1 = Course(program=p, title='Computer Science I', abbr='CS 140', description='The introduction to Computer Science')
    db.session.add(cs1)
    cs2 = Course(program=p, title='Computer Science II', abbr='CS 240', description='The introduction, continued.')
    db.session.add(cs2)
    dm = Course(program=p, title='Discrete Mathematics', abbr='MTH 242')
    db.session.add(dm)
    db.session.commit()

    # Add some units to a course
    cs1.units.extend(Area.query.get('SDF').units.all())
    db.session.add(cs1)
    db.session.commit()

