"""
Модели данных для БД.

Класы модели для базы данных.
"""

from app import db
from datetime import datetime


class Model(db.Model):
    """
    Класc для записи мат. моделей в БД.

    Перечень полей которые описывают мат. модль в БД.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True, unique=True)
    description = db.Column(db.String(200), index=True, unique=True)
    filename = db.Column(db.String(200), index=True, unique=True)
    measurement_variables = db.relationship('Measurementvariable',
                                            backref='Model', lazy='dynamic')
    signal_variables = db.relationship('Signalvariable', backref='Model',
                                       lazy='dynamic')
    achives = db.relationship('Achive', backref='Model', lazy='dynamic')

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {'id': self.id,
                'name': self.name,
                'description': self.description,
                'filename': self.filename,
                'measurement_variables': [item.serialize for item in self.measurement_variables],
                'signal_variables': [item.serialize for item in self.signal_variables]}

    def __repr__(self):
        return '<Model-{}>'.format(self.name)


class Measurementvariable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True, unique=False)
    register_number = db.Column(db.Integer)
    max_value = db.Column(db.Float)
    min_value = db.Column(db.Float)
    measurements = db.relationship('Measurement', backref='Variable',
                                   lazy='dynamic')
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {'id': self.id,
                'name': self.name,
                'register_number': self.register_number}

    def __repr__(self):
        return '<Variable - {}>'.format(self.name)


class Signalvariable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True, unique=False)
    bit_number = db.Column(db.Integer)
    measurements = db.relationship('Signal', backref='Variable',
                                   lazy='dynamic')
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {'id': self.id,
                'name': self.name,
                'bit_number': self.bit_number}

    def __repr__(self):
        return '<Variable - {}>'.format(self.name)


class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    value = db.Column(db.Float)
    achive_id = db.Column(db.Integer, db.ForeignKey('achive.id'))
    variable_id = db.Column(db.Integer,
                            db.ForeignKey('measurementvariable.id'))


class Signal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    value = db.Column(db.Integer)
    achive_id = db.Column(db.Integer, db.ForeignKey('achive.id'))
    variable_id = db.Column(db.Integer, db.ForeignKey('signalvariable.id'))


class Achive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    measurements = db.relationship('Measurement', backref='Achive',
                                   lazy='dynamic')
    signals = db.relationship('Signal', backref='Achive', lazy='dynamic')
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))

    def __repr__(self):
        return '<Achive id {} of task id {}>'.format(self.id, self.task_id)
