from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)
    tasks = db.relationship('Task', backref='author', lazy='dynamic')
    achives = db.relationship('Achive', backref='author', lazy='dynamic')
    def __repr__(self):
        return '<User {}>'.format(self.name)


class Modelselection(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), index = True, unique = True)
    description = db.Column(db.String(200))
    filename = db.Column(db.String(200))
    variables = db.relationship('Variable', backref = 'Modelselection', lazy = 'dynamic')
    achives = db.relationship('Achive', backref = 'Modelselection', lazy = 'dynamic')
    def __repr__(self):
        return '<Modelselection-{}>'.format(self.name)

class Variable(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), index = True, unique = False)
    regs = db.Column(db.Integer)
    max_value = db.Column(db.Float)
    min_value = db.Column(db.Float)
    measurements = db.relationship('Mesurement', backref = 'variable', lazy = 'dynamic')
    model_id = db.Column(db.Integer, db.ForeignKey('modelselection.id'))
    def __repr__(self):
        return '<Variable - {}>'.format(self.name)

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    time = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    value = db.Column(db.Float)
    achive_id = db.Column(db.Integer, db.ForeignKey('achive.id'))
    variable_id = db.Column(db.Integer, db.ForeignKey('variable.id'))
	
class State(db.Model):
    id=db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), index = True, unique = True)
    value = db.Column(db.Integer)
    description = db.Column(db.String(200))
	
class Achive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    datetime = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    measurements = db.relationship('Measurement', backref='achive', lazy='dynamic')
    def __repr__(self):
        return '<Achive id {} of task id {}>'.format(self.id, self.task_id)
		
