from flask import Flask,request,render_template,jsonify,url_for,make_response,redirect,session
from flask_sqlalchemy import SQLAlchemy
import json
import tools
from datetime import datetime, timedelta
import requests
from flask_bcrypt import Bcrypt
import googlemaps
import time

gmaps = googlemaps.Client(key='AIzaSyDEhgGJyZdVtKeprcaMXcS7KjDqbDKYG-8')
apiKey = "AIzaSyDEhgGJyZdVtKeprcaMXcS7KjDqbDKYG-8"
app = Flask(__name__)
app.secret_key = '\x9a{\xfc\x86(0\x92=Y\xaf-\xdf\x05z\x91\xadL+\xdeP\xa3w\xc0\x07'
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:kk@localhost/uberjr'
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    email = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    is_driver = db.Column(db.Boolean)
    driver_rel = db.relationship('Drivers', backref='users', primaryjoin='Users.id == Drivers.driver_id', uselist=False)
    rider_rel = db.relationship('Riders', backref='users', primaryjoin='Users.id == Riders.rider_id', uselist=False)

    def __init__(self, name, email, password, is_driver):
        self.name = name
        self.email = email
        self.password = password
        self.is_driver = is_driver

    def __repr__(self):
        return '<User %r>' % self.name

class Drivers(db.Model):
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    license_plate = db.Column(db.Text)
    car_color = db.Column(db.Text)
    car_year = db.Column(db.Text)
    car_make = db.Column(db.Text)
    is_active = db.Column(db.Boolean)
    timed_out = db.Column(db.Boolean)
    timeout_time = db.Column(db.Integer)
    active_rel = db.relationship('ActiveDrivers', backref='drivers', primaryjoin='Drivers.driver_id == ActiveDrivers.id', uselist=False)

    def __init__(self, driver_id, license_plate, car_color, car_year, car_make, is_active, timed_out, timeout_time):
        self.driver_id = driver_id
        self.license_plate = license_plate
        self.car_color = car_color
        self.car_year = car_year
        self.car_make = car_make
        self.is_active = is_active
        self.timed_out = timed_out
        self.timeout_time = timeout_time

    def __repr__(self):
        return '<Driver %r>' % self.license_plate

class ActiveDrivers(db.Model):
    __tablename__ = 'activedrivers'
    id = db.Column(db.Integer, db.ForeignKey('drivers.driver_id'), primary_key=True)
    current_lat = db.Column(db.Float)
    current_long = db.Column(db.Float)
    paired = db.Column(db.Boolean)
    paired_rel = db.relationship('Rides', backref='activedrivers', primaryjoin='ActiveDrivers.id == Rides.driver_id', uselist=False)

    def __init__(self, id, current_lat, current_long, paired):
        self.id = id
        self.current_lat = current_lat
        self.current_long = current_long
        self.paired = paired

    def __repr__(self):
        return '<ActiveDriver %r>' % self.id

class Riders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    origin_lat = db.Column(db.Float)
    origin_long = db.Column(db.Float)
    destination_lat = db.Column(db.Float)
    destination_long = db.Column(db.Float)
    paired = db.Column(db.Boolean)

    def __init__(self, rider_id, origin_lat, origin_long, destination_lat, destination_long, paired):
        self.rider_id = rider_id
        self.origin_lat = origin_lat
        self.origin_long = origin_long
        self.destination_lat = destination_lat
        self.destination_long = destination_long
        self.paired = paired

class Rides(db.Model):
    __tablename__ = 'rides'
    rider_id = db.Column(db.Integer)
    driver_id = db.Column(db.Integer, db.ForeignKey('activedrivers.id'), primary_key=True)
    pickup_lat = db.Column(db.Float)
    pickup_long = db.Column(db.Float)
    dest_lat = db.Column(db.Float)
    dest_long = db.Column(db.Float)
    accepted = db.Column(db.Boolean)
    pickedup = db.Column(db.Boolean)
    complete = db.Column(db.Boolean)

    def __init__(self, rider_id, driver_id, pickup_lat, pickup_long, dest_lat, dest_long, accepted, pickedup, complete):
        self.rider_id = rider_id
        self.driver_id = driver_id
        self.pickup_lat = pickup_lat
        self.pickup_long = pickup_long
        self.dest_lat = dest_lat
        self.dest_long = dest_long
        self.accepted = accepted
        self.pickedup = pickedup
        self.complete = complete

#ROUTES
@app.route("/")
def home():
    if 'email' in session:
        user = Users.query.filter_by(email = session['email']).first()
        if user.is_driver == True:
            return redirect(url_for('driver'))
        else:
            return redirect(url_for('rider'))
    else:
        return render_template("login.html")

@app.route("/driver")
def driver():
    if 'email' not in session:
        return redirect(url_for('login'))
    user = Users.query.filter_by(email = session['email']).first()
    if user.is_driver == False:
        return redirect(url_for('rider'))
    else:
        return render_template("driver.html")

@app.route("/rider")
def rider():
    if 'email' not in session:
        return redirect(url_for('login'))
    user = Users.query.filter_by(email = session['email']).first()
    if user.is_driver == True:
        return redirect(url_for('driver'))
    else:
        return render_template("rider.html")

@app.route("/signup")
def signup():
    if 'email' in session:
        user = Users.query.filter_by(email = session['email']).first()
        if user.is_driver == True:
            return redirect(url_for('driver'))
        else:
            return redirect(url_for('rider'))
    else:
        return render_template("signup.html")

@app.route("/login")
def login():
    if 'email' in session:
        user = Users.query.filter_by(email = session['email']).first()
        if user.is_driver == True:
            return redirect(url_for('driver'))
        else:
            return redirect(url_for('rider'))
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    if 'email' not in session:
        return redirect(url_for('login'))
    else:
        user = Users.query.filter_by(email = session['email']).first()
        if user.is_driver == True:
            # mark the driver as inactive
            driver = Drivers.query.filter_by(driver_id = user.id).first()
            if driver.is_active == True:
                driver.is_active = False
                # remove the driver from the activedrivers table
                ActiveDrivers.query.filter_by(id = user.id).delete()
                db.session.commit()
                session.pop('email', None)
                return redirect(url_for('home'))
            else:
                if driver.timed_out == True:
                    return redirect(url_for('driver'))
                else:
                    driver.is_active = False
                    # remove the driver from the activedrivers table
                    ActiveDrivers.query.filter_by(id = user.id).delete()
                    db.session.commit()
                    session.pop('email', None)
                    return redirect(url_for('home'))
        else:
            Riders.query.filter_by(rider_id=user.id).delete()
            db.session.commit()
            session.pop('email', None)
            return redirect(url_for('home'))

#return all available drivers in your area
@app.route("/api/getDrivers", methods=['POST'])
def getDrivers():
    lng = request.form.get('lng')
    lat = request.form.get('lat')
    #get all available drivers
    allDrivers = ActiveDrivers.query.filter_by(paired=False).all()
    #get all drivers who are some distance from rider
    for driver in allDrivers:
        print (driver)
        print (driver.current_lat)
        print (driver.current_long)
        print ("\n")
    #calculate average pickup time
    return "check it"

@app.route("/api/updateDriverLocation",methods=['POST'])
def updateDriverLocation():
    driver = Users.query.filter_by(email = session['email']).first()
    lng = request.form.get('lng')
    lat = request.form.get('lat')
    activeDriver = ActiveDrivers.query.filter_by(id= driver.id).first()
    if activeDriver is not None:
        activeDriver.current_long = lng
        activeDriver.current_lat = lat
        db.session.commit()
        return "updated driver\'s location"
    else:
        return "couldn't update driver\'s location because not active??"

#API for the frontend to request estimate travel time/cost based on user GPS location and destination Address
@app.route("/api/getTravelTime", methods=['POST'])
def api_getTravelInfo():
    originLongitude = request.json.get('longitude')
    originLatitude = request.json.get('latitude')
    destinationAddress = request.json.get('destinationAddress')
    estimatePickUpTime = request.json.get('estimatePickUpTime')

    originGPS ="%s,%s" % (originLatitude,originLongitude)

    #for now
    #get current systemtime
    departureTime = "now"

    #we should add departure time to this request based on the available drivers.
    #currently departure time is set to now.
    #departure time parameter is necessary to receive traffic information in the response.
    #there are 3 different modes for traffic calculation based on historical data. best_guess, pessimistic, optimistic.
    r = requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&key=%s&departure_time=%s" % (originGPS,destinationAddress,apiKey, departureTime))
    print (r)
    if r.status_code == 200:
        response = r.content
        travelTime, travelDistance = tools.extractTravelTime(response)
        travelCost = tools.calculateCost(travelTime,travelDistance)
        response = jsonify(estimateTime = travelTime, estimateCost = travelCost)
        print (response)
        return (response)
    else:
        return "error"

@app.route("/api/signup", methods=['POST'])
def api_signup():
    name = request.form.get('name')
    userEmail = request.form.get('email')
    password = request.form.get('password')
    confirmpassword = request.form.get('confirmpassword')
    status = request.form.get('isdriver')
    if (status == 'true'):
        licenseplate = request.form.get('licenseplate')
        color = request.form.get('color')
        year = request.form.get('year')
        make = request.form.get('make')
    user = Users.query.filter_by(email=userEmail).first()
    if user is None:
        if password == confirmpassword:
            hashedpw = bcrypt.generate_password_hash(password)
            if (status == 'true'):
                isDriver = True
            else:
                isDriver = False
            new_user = Users(name, userEmail, hashedpw, isDriver)
            db.session.add(new_user)
            db.session.commit()
            # if user is a driver, create an entry with car details in drivers table
            if (isDriver == True):
                # driver_id = corresponding user account's id (as a foreign key)
                driveid = Users.query.filter_by(email=userEmail).first().id
                new_driver = Drivers(driveid, licenseplate, color, year, make, False, False, 0)
                db.session.add(new_driver)
                db.session.commit()
                resp = make_response(url_for('driver'))
                session['email'] = new_user.email
                return resp
            else:
                resp = make_response(url_for('rider'))
                session['email'] = new_user.email
                return resp
    else:
        return status

@app.route("/api/login", methods=['POST'])
def api_login():
    userEmail = request.form.get('email')
    password = request.form.get('password')
    user = Users.query.filter_by(email=userEmail).first()
    if user is not None:
        #compare hashed password to hashed password in db
        if bcrypt.check_password_hash(user.password, password):
            #here we need to create a cookie for the client and return it along with the response
            if user.is_driver == True:
                print ('driver login succeeded')
                resp = make_response(url_for('driver'))
                session['email'] = user.email
                return resp
            else:
                print ('rider login succeeded')
                resp = make_response(url_for('rider'))
                session['email'] = user.email
                return resp
        else:
            print ('user\'s password is incorrect')
            return "Invalid password!"
    elif user is None:
        print ('user with that email does not exist')
        return "No account with that email was found!"
    else:
        return "No idea??"

@app.route("/api/checkTimedOut", methods=['GET'])
def api_checkTimedOut():
    driverid = Users.query.filter_by(email = session['email']).first().id
    driver = Drivers.query.filter_by(driver_id = driverid).first()
    if driver.timed_out == True:
        info = {'time': driver.timeout_time}
        return jsonify(info)
    else:
        return "false"

@app.route("/api/noTimeOut", methods=['POST'])
def api_noTimeOut():
    driverid = Users.query.filter_by(email = session['email']).first().id
    driver = Drivers.query.filter_by(driver_id = driverid).first()
    driver.timed_out = False
    db.session.commit()
    return "no longer timed out"

@app.route("/api/drive", methods=['POST'])
def api_drive():
    status = request.form.get('status')
    currentlat = request.form.get('originLat')
    currentlong = request.form.get('originLong')
    print('driver\'s current lat', currentlat)
    print('driver\'s current long', currentlong)
    if status == 'true':
        # mark the driver as 'active'
        driverid = Users.query.filter_by(email = session['email']).first().id
        driver = Drivers.query.filter_by(driver_id = driverid).first()
        driver.is_active = True
        db.session.commit()
        # add the driver to the active drivers table
        activedriverid = Drivers.query.filter_by(driver_id = driverid).first().driver_id
        new_active_driver = ActiveDrivers(activedriverid, currentlat, currentlong, False)
        db.session.add(new_active_driver)
        db.session.commit()
        return "added to ready to drive pool"

@app.route("/api/checkForRider", methods=['GET'])
def api_checkForRider():
    driverid = Users.query.filter_by(email = session['email']).first().id
    ride = Rides.query.filter_by(driver_id=driverid).first()
    # if ride request has been paired
    if ride is not None:
        # calculate ETA to rider's location here with distance matrix?
        pickup_eta = pickup_eta = datetime.now() + timedelta(seconds=921)
        # return response with rider's name, pickup location, and estimated pickup time
        ridername = Users.query.filter_by(id = ride.rider_id).first().name
        info = {'pickup_lat': ride.pickup_lat, 'pickup_long': ride.pickup_long, 'rider_name': ridername, 'pickup_eta': pickup_eta.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")}
        return jsonify(info)
    else:
        return "ride request not paired yet"

@app.route("/api/rider", methods=['POST'])
def api_rider():
    ### Origin
    origin = request.form.get('origin')
    geocode_origin = gmaps.geocode(origin)
    parsed_origin = json.loads(json.dumps(geocode_origin))
    origin_lat = parsed_origin[0][u'geometry'][u'location'][u'lat']
    origin_long = parsed_origin[0][u'geometry'][u'location'][u'lng']
    ### Destination
    destination = request.form.get('destination')
    geocode_destination = gmaps.geocode(destination)
    parsed_destination = json.loads(json.dumps(geocode_destination))
    destination_lat = parsed_destination[0][u'geometry'][u'location'][u'lat']
    destination_long = parsed_destination[0][u'geometry'][u'location'][u'lng']
    # rider_id = corresponding user account's id (as a foreign key)
    riderid = Users.query.filter_by(email = session['email']).first().id
    # add ride request to riders table
    ride = Riders(riderid, origin_lat, origin_long, destination_lat, destination_long, False)
    db.session.add(ride)
    db.session.commit()
    return "added ride request to table"

@app.route("/api/requestdriver", methods=['POST'])
def api_requestdriver():
    riderid = Users.query.filter_by(email = session['email']).first().id
    riderequest = Riders.query.filter_by(rider_id=riderid).first()
    if riderequest.paired == False:
        # origin of rider
        rider_origin = request.form.get('origin')
        rider_dest = request.form.get('destination')
        print('rider origin', rider_origin, ' rider dest', rider_dest)
        # calculate rider's current location gps coords
        geocode_rider_origin = gmaps.geocode(rider_origin)
        parsed_rider_origin = json.loads(json.dumps(geocode_rider_origin))
        rider_origin_lat = parsed_rider_origin[0][u'geometry'][u'location'][u'lat']
        rider_origin_long = parsed_rider_origin[0][u'geometry'][u'location'][u'lng']
        riderOriginGPS = "%s,%s" % (rider_origin_lat,rider_origin_long)

        geocode_rider_dest = gmaps.geocode(rider_dest)
        parsed_rider_dest = json.loads(json.dumps(geocode_rider_dest))
        rider_dest_lat = parsed_rider_dest[0][u'geometry'][u'location'][u'lat']
        rider_dest_long = parsed_rider_dest[0][u'geometry'][u'location'][u'lng']
        departureTime = "now"

        # for each active driver that hasn't been paired
        timeToRider = 1000000
        closestDriver = ActiveDrivers.query.filter_by(paired=False).first()
        if closestDriver is None:
            Riders.query.filter_by(rider_id=riderid).delete()
            db.session.commit()
            return "No drivers available. Check back later!"
        else:
            riderDestGPS = "%s,%s" % (rider_dest_lat,rider_dest_long)
            availdrivers = ActiveDrivers.query.filter_by(paired=False).all()
            # find closest driver
            for availdriver in availdrivers:
                # compute their current location's gps coords
                driverOriginGPS = "%s,%s" % (availdriver.current_lat,availdriver.current_long)
                # find closest driver in terms of travel time
                r = requests.get("https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=%s&destinations=%s&key=%s&departure_time=%s" % (driverOriginGPS,riderOriginGPS,apiKey,departureTime))
                #print r
                if r.status_code == 200:
                #if True:
                    response = r.content
                    parsed_response = json.loads(response)
                    print (parsed_response)
                    
                    if parsed_response[u'rows'][0][u'elements'][0][u'status'] != 'ZERO_RESULTS':
                        travelTime = parsed_response[u'rows'][0][u'elements'][0][u'duration_in_traffic'][u'value']
                    else:
                        travelTime = 1000
                    # if driver is within a range of 20 minutes away
                    if travelTime < 1200:
                        if travelTime < timeToRider:
                            timeToRider = travelTime
                            closestDriver = availdriver
            # calculate eta to destination with departuretime set to estimated pickup time
            depDestTime = int(time.time()) + timeToRider
            destDir = requests.get("https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=%s&destinations=%s&key=%s&departure_time=%s" % (riderOriginGPS,riderDestGPS,apiKey,depDestTime))
            if destDir.status_code == 200:
                destresponse = destDir.content
                parsed_destresp = json.loads(destresponse)
                if parsed_destresp[u'rows'][0][u'elements'][0][u'status'] != 'ZERO_RESULTS':
                    timeToDest = parsed_destresp[u'rows'][0][u'elements'][0][u'duration_in_traffic'][u'value']
                    milesToDest = parsed_destresp[u'rows'][0][u'elements'][0][u'distance'][u'value']
                    milesToDest = milesToDest / 1609.34
                    if milesToDest >= 100:
                        riderid = Users.query.filter_by(email = session['email']).first().id
                        Riders.query.filter_by(rider_id = riderid).delete()
                        db.session.commit()
                        return "destination is out of range/too far"
                else:
                    timeToDest = 1800
                    milesToDest = 55
            cost = tools.calculateCost(timeToDest, milesToDest)
            # mark the closest driver as paired
            closestDriver.paired = True
            # mark the ride request as paired
            riderequest.paired = True
            # pair the rider + driver & insert to rides table
            closestdriverid = ActiveDrivers.query.filter_by(id=closestDriver.id).first().id
            new_ride = Rides(riderid, closestdriverid, rider_origin_lat, rider_origin_long, rider_dest_lat, rider_dest_long, False, False, False)
            db.session.add(new_ride)
            db.session.commit()
            info = {'travelTime': timeToRider, 'fare': cost, 'timeToDest': timeToDest}
            return jsonify(info)
    else:
        return "can't request another ride! rider is already paired??"

@app.route("/api/checkRideAccepted", methods=['POST'])
def api_checkRideAccepted():
    riderid = Users.query.filter_by(email = session['email']).first().id
    riderequest = Riders.query.filter_by(rider_id=riderid).first()
    if riderequest is not None:
        if riderequest.paired == True:
            ride = Rides.query.filter_by(rider_id=riderid).first()
            if ride.accepted == True:
                timeToRider = request.form.get('timeToRider')
                timeToRider = int(timeToRider)
                drivername = Users.query.filter_by(id = ride.driver_id).first().name
                driverinfo = Drivers.query.filter_by(driver_id = ride.driver_id).first()
                pickup_eta = datetime.now() + timedelta(seconds=timeToRider)
                info = {'name': drivername, 'license_plate': driverinfo.license_plate, 'color': driverinfo.car_color, 'make': driverinfo.car_make, 'pickup_eta': pickup_eta.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")}
                return jsonify(info)
            else:
                return "ride request not accepted yet"
        else:
            return "ride request hasn't been paired yet or has been declined"
    else:
        return "ride request can't be checked for acceptance because no drivers available"

@app.route("/api/acceptDeclineRide", methods=['POST'])
def api_acceptDeclineRide():
    status = request.form.get('status')
    driverid = Users.query.filter_by(email = session['email']).first().id
    ride = Rides.query.filter_by(driver_id=driverid).first()
    riderid = ride.rider_id
    if status == 'accept':
        ride.accepted = True
        db.session.commit()
        return "ride accepted. ride marked accepted."
    else:
        # mark driver inactive
        driver = Drivers.query.filter_by(driver_id=driverid).first()
        driver.is_active = False
        # time out driver for 1 minute
        driver.timed_out = True
        driver.timeout_time = int(time.time()) + 60
        # remove driver from the activedrivers table
        ActiveDrivers.query.filter_by(id=driverid).delete()
        # return rider to ride request pool
        Rides.query.filter_by(driver_id=driverid).delete
        # set ride request to unpaired
        riderequest = Riders.query.filter_by(rider_id=riderid).first()
        riderequest.paired = False
        db.session.commit()
        return 'ride declined. driver marked inactive, and rider returned to ride request pool'

@app.route("/api/cancelRide", methods=['POST'])
def api_cancelRide():
    riderid = Users.query.filter_by(email = session['email']).first().id
    ride = Rides.query.filter_by(rider_id=riderid).first()
    driverid = ride.driver_id
    # remove ride
    Rides.query.filter_by(rider_id=riderid).delete()
    # remove ride request
    Riders.query.filter_by(rider_id = riderid).delete()
    # mark driver unpaired
    driver = ActiveDrivers.query.filter_by(id = driverid).first()
    driver.paired = False
    db.session.commit()
    return "ride canceled"

@app.route("/api/checkRideCanceled", methods=['GET'])
def api_checkRideCanceled():
    driverid = Users.query.filter_by(email = session['email']).first().id
    ride = Rides.query.filter_by(driver_id=driverid).first()
    if ride is None:
        driver = ActiveDrivers.query.filter_by(id = driverid).first()
        if driver.paired == False:
            return "ride has been canceled by rider. returned to pool"
    else:
        return "ride hasn't been canceled"

@app.route("/api/checkDriverLocation", methods=['GET'])
def api_checkDriveLocation():
    print ("*** checking driver's location....")
    riderid = Users.query.filter_by(email=session['email']).first().id
    ride = Rides.query.filter_by(rider_id=riderid).first()
    if ride is not None:
        driverid = ride.driver_id
        activeDriver = ActiveDrivers.query.filter_by(id=driverid).first()
        dest_lat = activeDriver.current_lat;
        dest_long = activeDriver.current_long;
        info = {'dest_lat': dest_lat,
                'dest_long': dest_long}
        print ("d_Lat", dest_lat, ", d_long", dest_long);
        return jsonify(info)
    else:
        return "none"

@app.route("/api/checkPickedUp", methods=['POST'])
def api_checkPickedUp():
    riderid = Users.query.filter_by(email = session['email']).first().id
    ride = Rides.query.filter_by(rider_id=riderid).first()
    if ride.pickedup == True:
        timeToRider = request.form.get('timeToRider')
        timeToDest = request.form.get('timeToDest')
        timeToRider = int(timeToRider)
        timeToDest = int(timeToDest)
        arrival_time = datetime.now() + timedelta(seconds=timeToRider+timeToDest)
        info = {'arrival_time': arrival_time.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")}
        return jsonify(info)
    else:
        return "false"

@app.route("/api/checkRideCompleted", methods=['GET'])
def api_checkRideCompleted():
    riderid = Users.query.filter_by(email = session['email']).first().id
    rider_ride = Riders.query.filter_by(rider_id=riderid).first()
    if rider_ride is None:
        return "true"
    else:
        return "false"

@app.route("/api/pickup", methods=['POST'])
def api_pickup():
    driverid = Users.query.filter_by(email = session['email']).first().id
    ride = Rides.query.filter_by(driver_id = driverid).first()
    if ride is not None:
        ride.pickedup = True
        db.session.commit()
        info = {'dest_lat': ride.dest_lat, 'dest_long': ride.dest_long}
        return jsonify(info)
    else:
        return "pickup failed; no ride found??"

@app.route("/api/completeRide", methods=['POST'])
def api_completeRide():
    driverid = Users.query.filter_by(email = session['email']).first().id
    ride = Rides.query.filter_by(driver_id = driverid).first()
    if ride is not None:
        # remove ride request
        Riders.query.filter_by(rider_id = ride.rider_id).delete()
        # remove paired ride
        Rides.query.filter_by(driver_id = driverid).delete()
        driver = ActiveDrivers.query.filter_by(id = driverid).first()
        driver.paired = False
        db.session.commit()
        return "ride request completed; driver is no longer paired"
    else:
        return "completing ride request failed; no ride found??"

@app.route("/api/inactive", methods=['POST'])
def api_inactive():
    user = Users.query.filter_by(email = session['email']).first()
    # mark the driver as inactive
    driver = Drivers.query.filter_by(driver_id = user.id).first()
    driver.is_active = False
    # remove the driver from the activedrivers table
    ActiveDrivers.query.filter_by(id = user.id).delete()
    db.session.commit()
    return "driver marked inactive."

if __name__ == '__main__':
    app.run(debug=True)
