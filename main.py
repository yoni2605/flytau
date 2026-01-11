from flask import render_template, Flask, redirect, request, session
from flask_session import Session
from datetime import timedelta, date
import mysql.connector
from contextlib import contextmanager
from utils import *
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)


app.config.update(
    SESSION_TYPE = 'filesystem',
    SESSION_FILE_DIR = '/flask_session_data',
    SESSION_PERMANENT = True,
    SESSION_PERMANENT_LIFETIME = timedelta(minutes=30),
    SESSION_COOKIE_SRCURE = True
)


Session(app)

@app.route('/')
def home_page():
    if 'fullname' in session:
        return redirect('/search_order_flights')
    elif 'namemgr' in session:
        return redirect('/homemgr/flights')
    return render_template('home_page.html')

@app.route('/logincust', methods=['GET','POST'])
def login_cust():
    if request.method == 'POST':
        mail = request.form.get('email')
        password = request.form.get('password')
        if checkcust(mail, password):
            session.clear()
            session['mail'] = mail
            session['fullname'] = getname(mail)
            return redirect('/search_order_flights')
        else:
            return render_template('login_cust.html', error='פרטי ההתחברות שגויים')
    return render_template('login_cust.html')

@app.route('/loginmgr', methods=['GET','POST'])
def loginman():
    if request.method == 'POST':
        id = request.form.get('id')
        password = request.form.get('password')
        if checkmgr(id, password):
            session.clear()
            session['id'] = id
            session['namemgr'] = getmgr(id)
            return redirect('/homemgr/flights')
        else:
            return render_template('login_manager.html', error='פרטי ההתחברות שגויים')
    return render_template('login_manager.html')

@app.route('/signup', methods=["POST", "GET"])
def sign_up():
    if request.method == 'POST':
        fullname = request.form.get('fullname').replace(" ", "")
        if fullname.isalpha() and fullname.isascii():
            session['fullname'] = request.form.get('fullname')
        else:
            return render_template('sign_up.html', error='נא להכניס שם מלא באנגלית בלבד')
        session['email'] = request.form.get('email')
        session['password'] = request.form.get('password')
        session['passport'] = request.form.get('passport')
        session['dob'] = request.form.get('dob')
        session['phonenums'] = int(request.form.get('phone_nums'))
        session['singup_date'] = date.today().isoformat()
        if mailexists(session['email']) == True:
            return render_template('sign_up.html', error='המייל קיים במערכת')
        return redirect('/phonenums')
    return render_template('sign_up.html', today=date.today().isoformat())

@app.route('/phonenums', methods=["POST", "GET"])
def insert_phones():
    if request.method == 'POST':
        session['phones'] = request.form.getlist('phones')
        new_user(session['fullname'], session['email'], session['password'], session['passport'], session['dob'], session['singup_date'], session['phones'])
        return redirect('/search_order_flights')
    return render_template('phonenums.html', phonenums = session['phonenums'])

@app.route('/search_order_flights')
def search_order_flights():
    name = session.get('fullname', 'guest')
    return render_template('search_order_flights.html', username=name, today=date.today().isoformat())

@app.route('/homemgr/flights')
def flightsmgr():
    filtered_date = request.args.get('date') or None
    origin = request.args.get('origin') or None
    destination = request.args.get('destination') or None
    status = request.args.get('status') or None

    flights = get_allflights_filtered(
        date=filtered_date,
        origin=origin,
        destination=destination,
        status=status
    )
    origins = get_origins()
    dests = get_dest()

    return render_template(
        'search_flightsmgr.html',
        flights=flights,
        admin_name=session['namemgr'],
        today=date.today().isoformat(),
        origins=origins,
        dests=dests
    )

@app.route('/homemgr/addemployee', methods=["POST", "GET"])
def addemployee():
    if request.method == 'POST':
        role = request.form.get('role')
        idemp = request.form.get('id')
        name = request.form.get('full_name_he')
        if not is_hebrew_name(name):
           return render_template('addemployee.html', error='שם העובד בעברית בלבד')
        phone = request.form.get('phone')
        if not idemp.isdigit():
            return render_template('addemployee.html', error='תעודת זהות חייבת להיות מספר בלבד')
        if not phone.isdigit():
            return render_template('addemployee.html', error='מספר טלפון חייב להיות מספר בלבד')
        startdate = request.form.get('start_date')
        istrained = request.form.get('long_flights_certified')
        city = request.form.get('city')
        street = request.form.get('street')
        house_num = request.form.get('house_number')
        if not add_employee(idemp,name,phone,startdate,role,istrained,city,street,house_num):
            return render_template('addemployee.html', error= 'תעודת הזהות של העובד קיימת במערכת')
        else:
            return render_template('addemployee.html', good='העובד נוסף בהצלחה למערכת')
    return render_template('addemployee.html')

@app.route('/homemgr/addflight', methods=["POST", "GET"])
def addflight():
    origins = get_origins()
    dests = get_dest()
    if request.method == 'POST':
        session['depdate'] = request.form.get('departure_date')
        session['deptime'] = request.form.get('departure_time')
        session['origin'] = request.form.get('origin')
        session['dest'] = request.form.get('dest')
        if session['origin'] == session['dest']:
            return render_template('addflight.html', origins=origins, dests=dests, error='לא ניתן לבחור טיסה עם מקור ויעד זהים', today=date.today().isoformat())
        return redirect('/homemgr/addflight/chooseaircrafts')
    return render_template('addflight.html', origins=origins, dests=dests, today=date.today().isoformat())

@app.route('/homemgr/addflight/chooseaircrafts', methods=["POST", "GET"])
def chooseaircrafts():
    if request.method == 'POST':
        session['aircraft'] = request.form.get('aircraft_id')
        return redirect('/homemgr/addflight/choosecrew')
    allaircrafts = get_specific_aricrafts(session['origin'], session['dest'], session['depdate'], session['deptime'])
    return render_template('chooseaircrafts.html', aircrafts=allaircrafts)


@app.route('/homemgr/addflight/choosecrew', methods=["POST", "GET"])
def choosecrew():
    route = get_route_by_origin_dest(session['origin'], session['dest'])
    duration = float(route[1])
    is_long = duration > 6.0
    aircraft = getaircraft_byid(session['aircraft'])
    size = aircraft[1]
    req_pilots = 3 if size == 'Large' else 2
    req_attendants = 6 if size == 'Large' else 3
    pilots = get_available_pilots(session['origin'], session['depdate'], session['deptime'], is_long)
    attendants = get_available_attendants(session['origin'], session['depdate'], session['deptime'], is_long)
    if request.method == "POST":
        pilot_ids = [x.strip() for x in request.form.getlist("pilot_ids") if x.strip()]
        attendant_ids = [x.strip() for x in request.form.getlist("attendant_ids") if x.strip()]
        errors = []
        if len(pilot_ids) != req_pilots:
            errors.append(f"חייב לבחור בדיוק {req_pilots} טייסים")
        if len(attendant_ids) != req_attendants:
            errors.append(f"חייב לבחור בדיוק {req_attendants} דיילים")
        if errors:
            return render_template(
                "choosecrew.html",
                available_pilots=pilots,
                available_attendants=attendants,
                req_pilots=req_pilots,
                req_attendants=req_attendants,
                origin=session["origin"],
                dest=session["dest"],
                depdate=session["depdate"],
                deptime=session["deptime"],
                error=" | ".join(errors)
            )
        session["chosen_pilots"] = pilot_ids
        session["chosen_attendants"] = attendant_ids
        return redirect("/homemgr/addflight/subflight")
    return render_template("choosecrew.html", available_pilots=pilots, available_attendants=attendants, origin=session["origin"], dest=session["dest"], depdate=session["depdate"], deptime=session["deptime"],req_pilots=req_pilots, req_attendants=req_attendants,)

@app.route('/homemgr/addflight/subflight', methods=["POST", "GET"])
def submitflight():
    origin = session["origin"]
    dest = session["dest"]
    depdate = session["depdate"]
    deptime = session["deptime"]
    aircraft_id = session["aircraft"]
    manufacturer, size = getaircraft_byid(aircraft_id)
    is_large = (size == "Large")
    pilot_ids = session.get("chosen_pilots", [])
    attendant_ids = session.get("chosen_attendants", [])
    pilots = get_employee_names_by_ids(pilot_ids)
    attendants = get_employee_names_by_ids(attendant_ids)
    if request.method == "POST":
        econ = request.form.get("economy_price", "").strip()
        bus = request.form.get("business_price", "").strip() if is_large else None
        errors = []
        try:
            econ_val = float(econ)
            if econ_val <= 0:
                errors.append("מחיר Economy חייב להיות גדול מ-0")
        except:
            errors.append("מחיר Economy לא תקין")
        if is_large:
            try:
                bus_val = float(bus)
                if bus_val <= 0:
                    errors.append("מחיר Business חייב להיות גדול מ-0")
            except:
                errors.append("מחיר Business לא תקין")
        else:
            bus_val = None

        if errors:
            return render_template(
                "submitflight.html",
                depdate=depdate, deptime=deptime, origin=origin, dest=dest,
                aircraft_id=aircraft_id, manufacturer=manufacturer, size=size,
                pilots=pilots, attendants=attendants,
                is_large=is_large,
                economy_price=econ,
                business_price=bus if bus is not None else "",
                error=" | ".join(errors)
            )

        create_flight_and_assign_crew(aircraft_id,origin,dest,depdate,deptime,econ_val,bus_val,pilot_ids,attendant_ids,"Scheduled")

        return redirect("/homemgr/flights")

    return render_template(
        "submitflight.html",
        depdate=depdate, deptime=deptime, origin=origin, dest=dest,
        aircraft_id=aircraft_id, manufacturer=manufacturer, size=size,
        pilots=pilots, attendants=attendants,
        is_large=is_large,
        economy_price="",
        business_price="",
        error=None
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
