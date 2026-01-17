from flask import render_template, Flask, redirect, request, session, flash
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
    SESSION_COOKIE_SECURE = True
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
            return render_template('sign_up.html', error='נא להכניס שם מלא באנגלית בלבד', today=date.today().isoformat())
        session['mail'] = request.form.get('email')
        session['password'] = request.form.get('password')
        session['passport'] = request.form.get('passport')
        session['dob'] = request.form.get('dob')
        session['phonenums'] = int(request.form.get('phone_nums'))
        session['singup_date'] = date.today().isoformat()
        if mailexists(session['mail']) == True:
            return render_template('sign_up.html', error='המייל קיים במערכת', today=date.today().isoformat())
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
    filtered_date = request.args.get('date') or None
    origin = request.args.get('origin') or None
    destination = request.args.get('destination') or None
    status = 'Scheduled' or None

    flights = get_allflights_filtered(
        date=filtered_date,
        origin=origin,
        destination=destination,
        status=status
    )
    origins = get_origins()
    dests = get_dest()

    return render_template(
        'search_order_flights.html',
        flights=flights,
        today=date.today().isoformat(),
        origins=origins,
        dests=dests,
        name=name)

@app.route("/search_order_flights/choosenumseat", methods=["GET", "POST"])
def choosenumseats():
    name = session.get('fullname', 'guest')

    if request.method == "GET":
        aircraft = request.args.get("aircraft")
        dep_date = request.args.get("dep_date")
        dep_time = request.args.get("dep_time")
        origin = request.args.get("origin")
        destination = request.args.get("destination")
        economy_price = request.args.get("economy_price")
        business_price = request.args.get("business_price")
        session["chosen_flight"] = {
            "aircraft": aircraft,
            "dep_date": dep_date,
            "dep_time": dep_time,
            "origin": origin,
            "destination": destination,
            "economy_price": economy_price,
            "business_price": None if business_price == "none" else business_price
        }
    chosen = session.get("chosen_flight", {})
    if request.method == "POST":
        session["numecon"] = request.form.get("seatsecon")
        if session["chosen_flight"]["business_price"] is not None:
            session["numbusi"] = request.form.get("seatsbusi")
        if 'numbusi' in session:
            if session["numecon"] == '0' and session["numbusi"] == '0':
                return render_template('numseats.html', error='בחר לפחות כרטיס אחד', name=name, econprice=chosen.get("economy_price"), busiprice=chosen.get("business_price"))
        else:
            if session["numecon"] == '0':
                return render_template('numseats.html', error='בחר לפחות כרטיס אחד', name=name, econprice=chosen.get("economy_price"), busiprice=chosen.get("business_price"))
        return redirect("/search_order_flights/choosenumseat/chooseseats")
    return render_template(
        "numseats.html",
        name=name,
        econprice=chosen.get("economy_price"),
        busiprice=chosen.get("business_price")
    )

@app.route("/search_order_flights/choosenumseat/chooseseats", methods=["POST", "GET"])
def chooseseats():
    name = session.get('fullname', 'guest')
    business_rows = 0
    business_cols = 0
    if session["chosen_flight"]["business_price"] is not None:
        business_rows, business_cols = get_class_layout(session['chosen_flight']['aircraft'], "Business")
    economy_rows, economy_cols = get_class_layout(session['chosen_flight']['aircraft'], "Economy")
    economy_start_row = business_rows + 1
    economy_end_row = business_rows + economy_rows
    taken_keys = get_taken_seat_for_flight(session['chosen_flight']['aircraft'], session['chosen_flight']['dep_date'], session['chosen_flight']['dep_time'])
    if request.method == 'POST':
        numecon = request.form.getlist('seatsecon')
        numbusi = request.form.getlist('seatsbusi')
        if len(numecon) != int(session["numecon"]):
            return render_template("chooseseats.html",
                        name=name,
                        aircraft_id=session['chosen_flight']['aircraft'],
                        dep_date=session['chosen_flight']['dep_date'],
                        dep_hour=session['chosen_flight']['dep_time'],
                        taken_keys=taken_keys,
                        business_rows=business_rows,
                        business_cols=business_cols,
                        economy_start_row=economy_start_row,
                        economy_end_row=economy_end_row,
                        economy_cols=economy_cols,
                        error=f"בחר בדיוק {session['numecon']} מושבים ב-Economy Class")
        if 'numbusi' in session:
            if len(numbusi) != int(session["numbusi"]):
                return render_template("chooseseats.html",
                                       name=name,
                                       aircraft_id=session['chosen_flight']['aircraft'],
                                       dep_date=session['chosen_flight']['dep_date'],
                                       dep_hour=session['chosen_flight']['dep_time'],
                                       taken_keys=taken_keys,
                                       business_rows=business_rows,
                                       business_cols=business_cols,
                                       economy_start_row=economy_start_row,
                                       economy_end_row=economy_end_row,
                                       economy_cols=economy_cols,
                                       error=f" בחר בדיוק {session['numbusi']} מושבים ב-Buisness Class")
        session['chosenecon'] = numecon
        session['chosenbusi'] = numbusi
        if name == 'guest':
            return redirect('/guest_details')
        return redirect('/submitorder')
    return render_template(
        "chooseseats.html",
        name=name,
        aircraft_id=session['chosen_flight']['aircraft'],
        dep_date=session['chosen_flight']['dep_date'],
        dep_hour=session['chosen_flight']['dep_time'],
        taken_keys=taken_keys,
        business_rows=business_rows,
        business_cols=business_cols,
        economy_start_row=economy_start_row,
        economy_end_row=economy_end_row,
        economy_cols=economy_cols,
    )

@app.route('/guest_details', methods=["POST", "GET"])
def guestdetails():
    name = session.get('fullname', 'guest')
    if request.method == 'POST':
        fullname = request.form.get('fullname').replace(" ", "")
        if fullname.isalpha() and fullname.isascii():
            session['guestname'] = request.form.get('fullname')
        else:
            return render_template('guest_details.html', error='נא להכניס שם מלא באנגלית בלבד', name=name, today=date.today().isoformat())
        session['guestemail'] = request.form.get('email')
        session['guestphonenums'] = int(request.form.get('phone_nums'))
        if mailexists(session['guestemail']) == True:
            return render_template('guest_details.html', error='המייל קיים במערכת', name=name, today=date.today().isoformat())
        return redirect('/phoneguest')
    return render_template('guest_details.html', name=name, today=date.today().isoformat())

@app.route('/phoneguest', methods=["POST", "GET"])
def phoneguest():
    if request.method == 'POST':
        session['phones'] = request.form.getlist('phones')
        return redirect('/submitorder')
    return render_template('phoneguest.html', phonenums = session['guestphonenums'])

@app.route('/submitorder', methods=["POST", "GET"])
def submitorder():
    if 'fullname' in session:
        name = session['fullname']
    else:
        name = session['guestname']
    flightdetails = session["chosen_flight"]
    econseats = session['chosenecon']
    busiseats = session['chosenbusi']
    totalprice = 0
    print(session['chosenecon'])
    print(session['chosenbusi'])
    if econseats is not None:
        totalprice += len(econseats) * float(flightdetails["economy_price"])
    if busiseats and flightdetails['business_price'] is not None:
        totalprice += len(busiseats) * float(flightdetails['business_price'])
    if request.method == 'POST':
        if 'guestemail' in session:
            new_guest(session['guestemail'], session['guestname'], session['phones'])
            orderid = insert_order_and_tickets(session['guestemail'], flightdetails['aircraft'], flightdetails['dep_date'], flightdetails['dep_time'], econseats, busiseats, flightdetails['economy_price'], flightdetails['business_price'], totalprice)
        elif "mail" in session:
            orderid = insert_order_and_tickets(session['mail'], flightdetails['aircraft'], flightdetails['dep_date'], flightdetails['dep_time'], econseats, busiseats, flightdetails['economy_price'], flightdetails['business_price'], totalprice)
        return render_template('approved.html', orderid=orderid, name=name)
    return render_template('submitorder.html', flightdetails=flightdetails, totalprice=totalprice, econseats=econseats, busiseats=busiseats)

@app.route("/guestorder", methods=["GET", "POST"])
def guestorder():
    name = session.get('fullname', 'guest')
    if request.method == 'POST':
        session['orderid'] = request.form.get('id')
        session['ordermail'] = request.form.get('mail')
        if order_exists_for_email(int(session['orderid']), session['ordermail']):
            session['order'], session['tickets'] = get_order_with_tickets(int(session['orderid']), session['ordermail'])
            return redirect('/cancel_order')
        else:
            return render_template('guestorder.html', error="ההזמנה לא נמצאה במערכת")
    return render_template("guestorder.html")

@app.route("/cancel_order", methods=["GET", "POST"])
def guestorder_details():
    name = session.get('fullname', 'guest')
    if request.method == 'POST':
        cancelled, massege = cancel_order_by_policy(int(session['orderid']),session['ordermail'])
        if cancelled is True:
            return render_template('guestorder_details.html',order=session['order'], tickets=session['tickets'], name=name, good=massege)
        else:
            return render_template('guestorder_details.html',order=session['order'], tickets=session['tickets'], name=name, error=massege)
    return render_template('guestorder_details.html', order=session['order'], tickets=session['tickets'], name=name)

@app.route('/custorder_details', methods=["GET", "POST"])
def custorder_details():
    name = session.get('fullname', 'guest')
    if 'mail' not in session:
        return redirect('/')
    email = session['mail']
    name = session.get('fullname', 'guest')
    status_filter = request.args.get('status')
    orders = get_custorders(email, status_filter)
    if request.method == "POST":
        order_id = request.form.get('order_id')
        cancelled, message = cancel_order_by_policy(int(order_id), email)
        orders = get_custorders(email, status_filter)
        return render_template("custorder_details.html",orders=orders,name=name,good=message if cancelled else None,error=None if cancelled else message)
    return render_template("custorder_details.html", orders=orders,name=name)

@app.route('/homemgr/flights')
def flightsmgr():
    aircraft_added = request.args.get("aircraft_added")
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
        dests=dests,
        good = "המטוס נוסף בהצלחה למערכת" if aircraft_added else None
    )

@app.route("/homemgr/cancelflight", methods=["POST", "GET"])
def cancel_flight():
    if request.method == 'POST':
        aircraft = request.form.get("aircraft")
        origin = request.form.get("origin")
        destination = request.form.get("destination")

        dep_date = datetime.strptime(
            request.form.get("departure_date"), "%Y-%m-%d"
        ).date()

        dep_time = datetime.strptime(
            request.form.get("departure_time"), "%H:%M:%S"
        ).time()

        ok, msg = cancel_flight_if_allowed(
            aircraft, dep_date, dep_time, origin, destination
        )

        flights = get_allflights_filtered()
        origins = get_origins()
        dests = get_dest()

        if ok:
            return render_template(
                "search_flightsmgr.html",
                flights=flights,
                origins=origins,
                dests=dests,
                today=date.today().isoformat(),
                good=msg,
                admin_name=session['namemgr']
            )
        else:
            return render_template(
                "search_flightsmgr.html",
                flights=flights,
                origins=origins,
                dests=dests,
                today=date.today().isoformat(),
                error=msg,
                admin_name=session['namemgr']
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

@app.route("/homemgr/addaircraft", methods=["POST", "GET"])
def addaircraft():
    if request.method == 'POST':
        id = request.form.get('id')
        if check_aircraft(id):
            return render_template('addaircraft.html', today=date.today().isoformat(), error='מזהה המטוס כבר קיים במערכת')
        new_Air = []
        new_Air.append(id)
        new_Air.append(request.form.get('manufacturer'))
        new_Air.append(request.form.get('parchasedate'))
        new_Air.append(request.form.get('size'))
        session['newaircraft'] = new_Air
        return redirect('/homemgr/addaircraft/chooseclass')
    return render_template('addaircraft.html', today=date.today().isoformat())

@app.route("/homemgr/addaircraft/chooseclass", methods=["POST", "GET"])
def chooseclass():
    if request.method == 'POST':
        ok, result = validate_seats(request.form.get("econrow"), request.form.get("econcol"), max_rows=25, max_cols=10)
        if not ok:
            return render_template("addairclass.html", error=result, size=session['newaircraft'][3])
        if session['newaircraft'][3] == 'Large':
            ok, result = validate_seats(request.form.get("buisnrow"), request.form.get("buisncol"), max_rows=5, max_cols=5)
            if not ok:
                return render_template("addairclass.html", error=result, size=session['newaircraft'][3])
        ecorow = request.form.get("econrow")
        ecocol = request.form.get("econcol")
        buisnrow = request.form.get("buisnrow")
        buiscol = request.form.get("buisncol")
        add_aircraft(session["newaircraft"],ecorow,ecocol,buiscol,buisnrow)
        return redirect('/homemgr/flights?aircraft_added=1')
    return render_template('addairclass.html', size=session['newaircraft'][3])

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

@app.before_request
def auto_update_flight_status():
    if request.path.startswith(("/search_order_flights", "/homemgr")):
        update_flights_status()
        update_flights_fully_booked()


if __name__ == '__main__':
    app.run(debug=True)
