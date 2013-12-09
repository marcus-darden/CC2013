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

    csm = Program(ont, 'CS Major [2014]', 'The Computer Science Major')
    db.session.add(csm)
    db.session.commit()

    cs1 = Course(csm, 'Computer Science I', 'CS 140', 'The introduction to Computer Science')
    db.session.add(cs1)
    cs2 = Course(csm, 'Computer Science II', 'CS 240', 'The introduction, continued.')
    db.session.add(cs2)
    dm = Course(csm, 'Discrete Mathematics', 'MTH 242')
    db.session.add(dm)
    db.session.commit()
