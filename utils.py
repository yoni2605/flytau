from flask import render_template, Flask, redirect, request, session
from flask_session import Session
from datetime import timedelta, date, datetime
import mysql.connector
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

def new_user(fullname, email, password, passport, dob, signup_date, phones):
    with mydb.cursor() as cursor:
        cursor.execute('INSERT INTO Customer(Email, Full_Name_Eng) VALUES (%s, %s)', (email, fullname))
        cursor.execute('INSERT INTO Registered_Customer(Email, passport_num, birth_date, joining_date, password) VALUES(%s, %s, %s, %s, %s)',(email, passport, dob, signup_date, password))
        for phone in phones:
            cursor.execute('INSERT INTO Phone_Numbers(Cust_Email, Phone_Num) VALUES(%s, %s)',(email, phone))

def mailexists(mail):
    with mydb.cursor() as cursor:
        cursor.execute('SELECT email FROM customer')
        allmails = [row[0] for row in cursor.fetchall()]
        if(str(mail) in allmails):
            return True
        return False

def checkcust(mail, password):
    with mydb.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM Registered_Customer WHERE Email = %s AND Password = %s",(mail, password))
        result = cursor.fetchone()
        return result is not None

def getname(mail):
    with mydb.cursor() as cursor:
        cursor.execute("SELECT Full_Name_Eng from customer WHERE Email = %s", (mail,))
        result = cursor.fetchone()
    return result[0]

def checkmgr(id, password):
    with mydb.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM Manager WHERE ID = %s AND Login_pass = %s", (id, password))
        result = cursor.fetchone()
        return result is not None

def getmgr(id):
    with mydb.cursor() as cursor:
        cursor.execute("SELECT Full_Name_Heb from employee WHERE id = %s", (id,))
        result = cursor.fetchone()
    return result[0]

def is_hebrew_name(name):
    for char in name:
        if not ('א' <= char <= 'ת' or char == ' '):
            return False
    return True

def add_employee(id,fullname,phone,startdate,role,istrained,city,street,housenum):
    with mydb.cursor() as cursor:
        cursor.execute('SELECT 1 FROM employee WHERE id = %s',(id,))
        result = cursor.fetchone()
        if result:
            return False
        else:
            if role == 'crew':
                cursor.execute(
                    'INSERT INTO employee(id, full_name_heb, phone_num, start_work_date, role) VALUES(%s, %s, %s, %s, %s)',
                    (id, fullname, phone, startdate, 'Flight_Attendant'))
                cursor.execute('INSERT INTO flight_attendent(id, long_dist_training) VALUES(%s, %s)',(id,istrained))
            elif role == 'pilot':
                cursor.execute(
                    'INSERT INTO employee(id, full_name_heb, phone_num, start_work_date, role) VALUES(%s, %s, %s, %s, %s)',
                    (id, fullname, phone, startdate, 'Pilot'))
                cursor.execute('INSERT INTO pilot(id, long_dist_training) VALUES(%s, %s)',(id,istrained))
            cursor.execute('INSERT INTO address(id, city, street, house_num) VALUES(%s, %s, %s, %s)', (id, city, street, housenum))
            return True


def get_origins():
    with mydb.cursor() as cursor:
        cursor.execute('SELECT DISTINCT(origin) FROM route')
        origins = [row[0] for row in cursor.fetchall()]
        return origins

def get_dest():
    with mydb.cursor() as cursor:
        cursor.execute('SELECT DISTINCT(destination) FROM route')
        dests = [row[0] for row in cursor.fetchall()]
        return dests
from datetime import datetime, timedelta

def calculate_arrival_datetime(dep_date, dep_hour, duration):
    return datetime.combine(dep_date, dep_hour) + timedelta(hours=duration)

def get_route_by_origin_dest(origin, destination):
    with mydb.cursor() as cursor:
        cursor.execute(
            "SELECT Route_ID, Duration FROM Route WHERE Origin=%s AND Destination=%s",
            (origin, destination)
        )
        return cursor.fetchone()

def get_all_aircrafts():
    with mydb.cursor() as cursor:
        cursor.execute("SELECT Air_Craft_ID, Size FROM Air_Craft")
        return cursor.fetchall()

def get_all_pilots():
    with mydb.cursor() as cursor:
        cursor.execute("""
            SELECT e.ID, p.Long_Dist_Training
            FROM Employee e
            JOIN Pilot p ON e.ID = p.ID
        """)
        return cursor.fetchall()

def get_all_attendants():
    with mydb.cursor() as cursor:
        cursor.execute("""
            SELECT e.ID, f.Long_Dist_Training
            FROM Employee e
            JOIN Flight_attendent f ON e.ID = f.ID
        """)
        return cursor.fetchall()

def get_last_landing_aircraft(aircraft_id):
    with mydb.cursor() as cursor:
        cursor.execute("""
            SELECT f.Arrival_Date, f.Arrival_Time, r.Destination
            FROM Flight f
            JOIN Route r ON f.Route_ID = r.Route_ID
            WHERE f.Air_Craft_ID=%s
            ORDER BY f.Arrival_Date DESC, f.Arrival_Time DESC
            LIMIT 1
        """, (aircraft_id,))
        return cursor.fetchone()

def get_future_flights_aircraft(aircraft_id, dep_date, dep_hour):
    with mydb.cursor() as cursor:
        cursor.execute("""
            SELECT r.Origin
            FROM Flight f
            JOIN Route r ON f.Route_ID=r.Route_ID
            WHERE f.Air_Craft_ID=%s
            AND (f.Dep_Date>%s OR (f.Dep_Date=%s AND f.Dep_Hour>%s))
        """, (aircraft_id, dep_date, dep_date, dep_hour))
        return cursor.fetchall()

def get_last_landing_employee(emp_id):
    with mydb.cursor() as cursor:
        cursor.execute("""
            SELECT f.Arrival_Date, f.Arrival_Time, r.Destination
            FROM Flight_Crew fc
            JOIN Flight f ON fc.Air_Craft_ID=f.Air_Craft_ID
                         AND fc.Dep_Date=f.Dep_Date
                         AND fc.Dep_Hour=f.Dep_Hour
            JOIN Route r ON f.Route_ID=r.Route_ID
            WHERE fc.ID=%s
            ORDER BY f.Arrival_Date DESC, f.Arrival_Time DESC
            LIMIT 1
        """, (emp_id,))
        return cursor.fetchone()

def get_future_flights_employee(emp_id, dep_date, dep_hour):
    with mydb.cursor() as cursor:
        cursor.execute("""
            SELECT r.Origin
            FROM Flight_Crew fc
            JOIN Flight f ON fc.Air_Craft_ID=f.Air_Craft_ID
                         AND fc.Dep_Date=f.Dep_Date
                         AND fc.Dep_Hour=f.Dep_Hour
            JOIN Route r ON f.Route_ID=r.Route_ID
            WHERE fc.ID=%s
            AND (f.Dep_Date>%s OR (f.Dep_Date=%s AND f.Dep_Hour>%s))
        """, (emp_id, dep_date, dep_date, dep_hour))
        return cursor.fetchall()

def aircraft_available(ac, origin, dep_date, dep_hour, duration):
    last = get_last_landing_aircraft(ac[0])
    if last:
        arr_dt = datetime.combine(last[0], last[1])
        if last[2] != origin or arr_dt > datetime.combine(dep_date, dep_hour):
            return False
    for f in get_future_flights_aircraft(ac[0], dep_date, dep_hour):
        if f[0] != origin:
            return False
    if ac[1] == "small" and duration > 6:
        return False
    return True

def employee_available(emp, origin, dep_date, dep_hour, duration):
    last = get_last_landing_employee(emp[0])
    if last:
        arr_dt = datetime.combine(last[0], last[1])
        if last[2] != origin or arr_dt > datetime.combine(dep_date, dep_hour):
            return False
    for f in get_future_flights_employee(emp[0], dep_date, dep_hour):
        if f[0] != origin:
            return False
    if duration > 6 and not emp[1]:
        return False
    return True

def get_available_resources(dep_date, dep_hour, origin, destination):
    route = get_route_by_origin_dest(origin, destination)
    if not route:
        return [], [], []

    route_id, duration = route

    aircrafts = [ac for ac in get_all_aircrafts()
                 if aircraft_available(ac, origin, dep_date, dep_hour, duration)]

    pilots = [p for p in get_all_pilots()
              if employee_available(p, origin, dep_date, dep_hour, duration)]

    attendants = [a for a in get_all_attendants()
                  if employee_available(a, origin, dep_date, dep_hour, duration)]

    available_aircrafts = []
    selected_pilots = []
    selected_attendants = []

    for ac in aircrafts:
        if ac[1] == "small":
            if len(pilots) >= 2 and len(attendants) >= 3:
                available_aircrafts.append(ac)
                selected_pilots.extend(pilots[:2])
                selected_attendants.extend(attendants[:3])
        else:
            if len(pilots) >= 3 and len(attendants) >= 6:
                available_aircrafts.append(ac)
                selected_pilots.extend(pilots[:3])
                selected_attendants.extend(attendants[:6])

    return available_aircrafts, selected_pilots, selected_attendants

