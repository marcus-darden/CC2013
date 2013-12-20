from CC2013 import app, db, oid, lm
from CC2013.models import *

ont = User.query.get(1)

if ont and ont.nickname == 'Ontoral':
    csm = Program.query.get(1)
else:
    ont = User()
    ont.nickname = 'Ontoral'
    ont.email = 'ontoral@gmail.com'
    db.session.add(ont)
    db.session.commit()

    csm = Program(user=ont, title='CS Major [2014]', description='The Computer Science Major')
    db.session.add(csm)
    db.session.commit()

    cs1 = Course(program=csm, title='Computer Science I', abbr='CS 140', description='The introduction to Computer Science')
    db.session.add(cs1)
    cs2 = Course(program=csm, title='Computer Science II', abbr='CS 240', description='The introduction, continued.')
    db.session.add(cs2)
    dm = Course(program=csm, title='Discrete Mathematics', abbr='MTH 242')
    db.session.add(dm)
    db.session.commit()

    cs1.units.extend(Area.query.get('SDF').units.all())
    db.session.add(cs1)
    db.session.commit()
