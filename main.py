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

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)


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
        return redirect('/homemgr')
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
            return redirect('/homemgr')
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
        if(mailexists(session['email']) == True):
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

@app.route('/homemgr')
def homemgr():
    return render_template('homemgr.html', admin_name=session['namemgr'])

@app.route('/homemgr/flights')
def flightsmgr():
    return render_template('search_flightsmgr.html', flights='')

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
            return render_template('addflight.html', origins=origins, dests=dests, error='לא ניתן לבחור טיסה עם מקור ויעד זהים')
        return redirect('/homemgr/addflight/addcrew')
    return render_template('addflight.html', origins=origins, dests=dests)

@app.route('/homemgr/addflight/addcrew', methods=["POST", "GET"])
def addcrew():
    depdate = datetime.strptime(session['depdate'], "%Y-%m-%d").date()
    deptime = datetime.strptime(session['deptime'], "%H:%M").time()
    available_aircrafts, selected_pilots, selected_attendants = get_available_resources(depdate, deptime, session['origin'], session['dest'])
    return render_template('addcrew.html',origin=session['origin'],dest=session['dest'],deptime=session['deptime'],depdate=session['depdate'], available_aircrafts=available_aircrafts, available_pilots=selected_pilots, available_attendants=selected_attendants)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)