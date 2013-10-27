#!/usr/bin/env python

import csv

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'Computing Curricula 2013'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
db = SQLAlchemy(app)


class KA(db.Model):
    __tablename__ = 'ka'
    id = db.Column(db.String(3), primary_key=True)
    text = db.Column(db.String(64))
    kus = db.relationship('KU', backref='kas', lazy='dynamic')
    outcomes = db.relationship('Outcome', backref='kas', lazy='dynamic')

    def __init__(self, id, text):
        self.id = id.strip().upper()
        self.text = text.strip()

    def __repr__(self):
        return '<Knowledge Area: {0.id}>'.format(self)


class KU(db.Model):
    __tablename__ = 'ku'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(64))
    tier1 = db.Column(db.Float)
    tier2 = db.Column(db.Float)
    elective = db.Column(db.Float)
    ka_id = db.Column(db.String, db.ForeignKey('ka.id'))
    #outcomes = db.relationship('Outcome', backref='kus', lazy='dynamic')

    def __init__(self, ka, text, tier1, tier2):
        self.text = text.strip()
        self.tier1 = tier1
        self.tier2 = tier2
        self.ka_id = ka.strip().upper()

    def __str__(self):
        return '<Knowledge Unit: {0.text} KA: {0.ka_id}>'.format(self)


class Mastery(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    text = db.Column(db.String(16))
    outcomes = db.relationship('Outcome', backref='kus', lazy='dynamic')

    def __init__(self, id, text):
        self.id = id
        self.text = text

    def __str__(self):
        return '<Mastery: {0.text}>'.format(self)


class Outcome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(256))
    tier = db.Column(db.Integer)
    mastery_id = db.Column(db.Integer, db.ForeignKey('mastery.id'))
    number = db.Column(db.Integer)
    ka_id = db.Column(db.String, db.ForeignKey('ka.id'))
    ku_id = db.Column(db.Integer, db.ForeignKey('ku.id'))

    def __init__(self, ka, ku, tier, mastery, number, text):
        self.tier = tier
        self.number = number
        self.text = text.strip()

        mastery_id = Mastery.query.filter_by(master).first().id
        self.ka_id = ka.strip().upper()

    def __repr__(self):
        return str(self.__dict__)
        return '<Outcome: {0.text}>'.format(self)


@app.route('/')
def index():
    kas = KA.query.all()
    for ka in kas:
        print ka
    masteries = Mastery.query.all()
    for mastery in masteries:
        print mastery
    return 'It works!'


# Initialize the database
@app.before_first_request
def init_db():
    db.create_all()

    # Initialize Knowledge Areas (KA)
    with open('csv/ka.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                ka = KA(*row)
                db.session.add(ka)

    # Initialize Masteries
    for index, description in enumerate(['Familiarity', 'Usage', 'Assessment']):
        mastery = Mastery(index + 1, description)
        db.session.add(mastery)

    db.session.commit()


if __name__ == '__main__':
    app.run()

