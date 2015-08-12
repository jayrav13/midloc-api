from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from secret import PYMYSQL_SECRET_KEY

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = PYMYSQL_SECRET_KEY
db = SQLAlchemy(app)

class Zipcodes(db.Model):
	__tablename__ = 'zipcodes'

	id = db.Column(db.Integer, primary_key=True)
	postal_code = db.Column(db.String, unique=True)
	latitude = db.Column(db.Float(precision=4), unique=True)
	longitude = db.Column(db.Float(precision=5), unique=True)

	def __init__(self, postal_code):
		self.postal_code = postal_code

class Users(db.Model):
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String, unique=True)
	password = db.Column(db.String)
	access_key = db.Column(db.String)
	request_count = db.Column(db.Integer)

	def __init__(self, email, password, access_key):
		self.email = email
		self.password = password
		self.access_key = access_key
		self.request_count = 1

class Register(db.Model):
	__tablename__ = "register"

	id = db.Column(db.Integer, primary_key=True)
	ip = db.Column(db.String)
	datetime = db.Column(db.String)
	illegal_register = db.Column(db.Integer)
	legal_register = db.Column(db.Integer)

	def __init__(self, ip, datetime):
		self.ip = ip
		self.datetime = datetime
		self.illegal_register = 0
		self.legal_register = 1
