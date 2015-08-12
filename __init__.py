from flask import abort, Flask, jsonify, redirect, request, make_response, render_template
#from flask.ext.assets import Environment, Bundle
from model import Register, Users, Zipcodes, db
from secret import GOOGLE_SECRET_KEY
import hashlib
import requests
import json
import datetime
import time
from decimal import Decimal

app = Flask(__name__)

#assets = Environment(app)

###
# Home route - currently redirects to jayravaliya.com
###
@app.route("/")
def home():
	return redirect('http://jayravaliya.com')

###
# Will be the total "documentation" for this API
###
@app.route("/api", methods=['GET'])
def introduction():
	reg = Register(request.remote_addr, time.time())
	db.session.add(reg)
	db.session.commit()
	return jsonify(
		{
			'welcome':'Welcome to Midloc\'s RESTful API.', 
			'info':
				{
					'midloc-by':'Jay Ravaliya (@jayrav13) and Lee Weisberger',
					'platforms':'iOS, Android',
					'tech':'This API is built using Python\'s Flask microframework, using SQLAlchemy to connect to a MySQL database hosted on Linode.'
				},
			'docs':
				{
					'register':
					{
						'request':'Register by sending a cURL request to /api/register (via POST) with parameters \"email\" and \"password\" in cleartext.',
						'security':'Password will be stored in its encrypted form after request is sent.',
						'access_key':'A value called \"access_key\" will be returned. This must be used to make all requests to the primary endpoint.'
					},
					'endpoint':
					{
						'request':'A request can be sent to the endpoint, found at /api/v1.0/endpoint (via GET) woth parameters \"you\", \"friend\" and \"access_key\"',
						'patterns':
						{
							'zip_code':'A five digit number. (ex. \"07470\")',
							'coordinates':'Two floating point numbers, separated by a single comma. (ex. \"40.9459,-74.2451\")',
							'address':'Anything that doesn\'t fall into the above two categories will be registered as an address.'
						}
					}
				}
		}
	)

###
# Main endpoint for this API
###
@app.route("/api/v1.0/endpoint", methods=['GET'])
def endpoint():
	# Abort 400 if proper parameters aren't set
	if not request.args['you'] or not request.args['friend'] or not request.args['access_key']:
		abort(400)

	else:
		# Abort 401 if user is not found
		user = Users.query.filter_by(access_key=request.args['access_key']).first()
		if not user:
			abort(401)

		# Increment count number for user.
		user.request_count = user.request_count + 1
		db.session.commit()
		
		# Method to determine if a string is a floating point value or not
		def isFloat(string):
			try:
				float(string)
				return True
			except ValueError:
				return False

		# Method to parse the inputs and determine course of action
		def evaluate(var):	
			# Pattern for Zip Code - 5 characters, all digits
			if var.isdigit() and len(var) == 5:
				zip = Zipcodes.query.filter_by(postal_code=var).first()
				if not zip:
					return [999,999]
				else:
					return [zip.latitude, zip.longitude]
			else:
				arr = var.split(',', 1)
				# Pattern for Coordinates - if input can be split into an array of 2 values using comma as a deliminator and both are floating
				# point values
				if len(arr) == 2 and isFloat(arr[0]) and isFloat(arr[1]):
					return arr
				
				# Error if input is non-Zip Code but all numeric
				elif var.isdigit() and len(var) != 5:
					return [999,999]
				
				# Handle as an address - push to Google Geocode API.	
				else:
					parameters = {'address':var,'key':GOOGLE_SECRET_KEY}
					r = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=parameters).json()
					return r['results'][0]['geometry']['location']['lat'], r['results'][0]['geometry']['location']['lng']

		def midpoint(yLoc, fLoc):
			return [(Decimal(yLoc[0]) + Decimal(fLoc[0])) / 2, (Decimal(yLoc[1]) + Decimal(fLoc[1])) / 2]		
	
		def googlePlaces(midpoint, locationType):
			parameters = {
				'location':str(midpoint[0]) + "," + str(midpoint[1]),
				'rankby':'distance',
				'types':'restaurant',
				'key':GOOGLE_SECRET_KEY		
			}		
			r = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json",params=parameters)
			requestJSON = r.json()
			if requestJSON['status'] == 'ZERO_RESULTS':
				return make_response(jsonify({'error':'ZERO_RESULTS'}),404)
			else:
				return jsonify(**r.json())

		# Return the result of the evaluate method on contents of "you"
		yourLoc = evaluate(request.args['you'])
		friendLoc = evaluate(request.args['friend'])

		if yourLoc == friendLoc:
			return make_response(jsonify({'error':'SAME_LOCATIONS'}), 400)	
		else:
			midpoint = midpoint(yourLoc, friendLoc)
			return googlePlaces(midpoint, "restaurant")

###
# Registes a new user. First checks to confirm that POST parameters are set and email address is not registered yet.
# Disallows users from registering from the same IP within 60 seconds of each other.
###
@app.route('/api/register', methods=['POST'])
def register():
	reg = Register.query.filter_by(ip=request.remote_addr).first()

	if reg:
		if Decimal(time.time()) - Decimal(reg.datetime) < 60.0:
			return make_response(jsonify({'error':'FREQUENT_REGISTRATION','notes':'Wait 60 seconds between registering from the same IP.'}), 400)
		else:
			reg.datetime = time.time()
	else:
		reg = Register(request.remote_addr, time.time())
		db.session.add(reg)
		
	db.session.commit()
	
	if not request.form['email'] or not request.form['password']:
		abort(400)
	elif Users.query.filter_by(email=request.form['email']).first():
		abort(409)
	else:
		user = Users(request.form['email'], hashlib.md5(request.form['password']).hexdigest(), hashlib.md5(request.form['email'] + ":" + str(time.time())).hexdigest())
		db.session.add(user)
		db.session.commit()		
		return jsonify({'Success':request.form['email'] + ' registered under access key ' + user.access_key,'access_key':user.access_key})

###
# Error Handlers
###
@app.errorhandler(400)
def invalid_usage(error):
	return make_response(jsonify({'Invalid Usage':'This operation was not used correctly. Visit /api to learn about proper usage.'}), 400)

@app.errorhandler(409)
def username_taken(error):
	return make_response(jsonify({'Resource Conflict':'This email is already registered - please try another!'}))

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'Not Found':'This request was not found. Visit /api to learn about proper usage.'}), 400)

@app.errorhandler(401)
def unauthorized(error):
	return make_response(jsonify({'Unauthorized':'This operation requires an access key! Visit /api to learn more about proper usage.'}), 401)

@app.errorhandler(405)
def invalid_method(error):
	return make_response(jsonify({'Invalid Method':'You used a request type that was not permitted. Visit /api to learn more about proper usage.'}), 405)

###
# RUN
###
if __name__ == "__main__":
	app.run(host='45.33.69.6', debug=True)


