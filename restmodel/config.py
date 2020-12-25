import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # ...
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@127.0.0.1:6543/tppsim'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
