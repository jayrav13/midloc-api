from flask import Flask, jsonify, redirect, request, make_response, render_template
from model import Zipcodes, db
import os
from secret import GOOGLE_SECRET_KEY
import requests
import json

app = Flask(__name__)

@app.route("/")
def home():
	return redirect('http://jayravaliya.com')

@app.route("/api")
def introduction():
	return jsonify(
		{'welcome':'Welcome to Midloc\'s RESTful API.', 
		'info':
			{'details':'Visit http://midloc.jayravaliya.com/api/docs for usage.',
			'tech':'This API is built using Python\'s Flask microframework, using SQLAlchemy to connect to a MySQL database hosted on Linode.'}
		}
	)

@app.route("/api/docs")
def documentation():
	return jsonify(
		{'documentation':
			{'endpoint':'/api/v1.0/endpoint','request':{'method':'GET','parameters':'you, friend'}}
		}
	)

@app.route("/api/v1.0/endpoint", methods=['GET'])
def endpoint():
	if not request.args['you'] or not request.args['friend']:
		abort(400)
	else:
		def isFloat(string):
			try:
				float(string)
				return True
			except ValueError:
				return False

		def evaluate(var):	
			if var.isdigit() and len(var) == 5:
				zip = Zipcodes.query.filter_by(postal_code=var).first()
				return jsonify({'identified_as':'zipcode','coordinates':{'latitude':str(zip.latitude),'longitude':str(zip.longitude)}})
			else:
				arr = var.split(',', 1)
				if len(arr) == 2 and isFloat(arr[0]) and isFloat(arr[1]):
					return jsonify({'identified_as':'coordinates','coordinates':{'latitude':arr[0],'longitude':arr[1]}})
				elif var.isdigit() and len(var) != 5:
					return jsonify({'error':'Invaid input.'})
				else:
					parameters = {'address':var,'key':GOOGLE_SECRET_KEY}
					r = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=parameters)
					#return json.loads(r.text)
					return jsonify(**r.json())

		return evaluate(request.args['you'])

@app.errorhandler(400)
def invalid_usage(error):
	return make_response(jsonify({'Invalid usage':'Visit /api/docs to learn about proper usage.'}), 400)

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'Not found':'Visit api/docs to learn about proper usage.'}), 400)

if __name__ == "__main__":
	app.run(host='45.33.69.6', debug=True)


