from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash



class Model(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), index = True, unique = True)
    description = db.Column(db.String(200),index = True, unique = True)
    filename = db.Column(db.String(200),index = True, unique = True)
    variables = db.relationship('Variable', backref = 'Model', lazy = 'dynamic')
    achives = db.relationship('Achive', backref = 'Model', lazy = 'dynamic')
    def __repr__(self):
        return '<Modelselection-{}>'.format(self.name)

class Variable(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), index = True, unique = False)
    register_number = db.Column(db.Integer)
    modbus_unit = db.Column(db.Integer)
    max_value = db.Column(db.Float)
    min_value = db.Column(db.Float)
    measurements = db.relationship('Measurement', backref = 'Variable', lazy = 'dynamic')
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    def __repr__(self):
        return '<Variable - {}>'.format(self.name)

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    time = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    value = db.Column(db.Float)
    achive_id = db.Column(db.Integer, db.ForeignKey('achive.id'))
    variable_id = db.Column(db.Integer, db.ForeignKey('variable.id'))

class Achive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, index = True, default = datetime.utcnow)
    measurements = db.relationship('Measurement', backref='Achive', lazy='dynamic')
    def __repr__(self):
        return '<Achive id {} of task id {}>'.format(self.id, self.task_id)
