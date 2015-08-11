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

