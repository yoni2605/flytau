import os
from contextlib import contextmanager
from datetime import datetime, timedelta
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=True,
        connection_timeout=5
    )


@contextmanager
def db_cursor(dictionary: bool = False):
    db = get_db()
    cur = db.cursor(dictionary=dictionary)
    try:
        yield cur
        db.commit()
    finally:
        try:
            cur.close()
        finally:
            db.close()



def new_user(fullname, email, password, passport, dob, signup_date, phones):
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO Customer(Email, Full_Name_Eng) VALUES (%s, %s)",
            (email, fullname)
        )
        cursor.execute(
            "INSERT INTO Registered_Customer(Email, passport_num, birth_date, joining_date, password) VALUES(%s, %s, %s, %s, %s)",
            (email, passport, dob, signup_date, password)
        )
        for phone in phones:
            cursor.execute(
                "INSERT INTO Phone_Numbers(Cust_Email, Phone_Num) VALUES(%s, %s)",
                (email, phone)
            )


def mailexists(mail):
    with db_cursor() as cursor:
        cursor.execute("SELECT email FROM customer")
        allmails = [row[0] for row in cursor.fetchall()]
        return str(mail) in allmails


def checkcust(mail, password):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM Registered_Customer WHERE Email = %s AND Password = %s",
            (mail, password)
        )
        return cursor.fetchone() is not None


def getname(mail):
    with db_cursor() as cursor:
        cursor.execute("SELECT Full_Name_Eng from customer WHERE Email = %s", (mail,))
        result = cursor.fetchone()
    return result[0] if result else None


def checkmgr(id, password):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM Manager WHERE ID = %s AND Login_pass = %s",
            (id, password)
        )
        return cursor.fetchone() is not None


def getmgr(id):
    with db_cursor() as cursor:
        cursor.execute("SELECT Full_Name_Heb from employee WHERE id = %s", (id,))
        result = cursor.fetchone()
    return result[0] if result else None


def is_hebrew_name(name):
    for char in name:
        if not ("א" <= char <= "ת" or char == " "):
            return False
    return True

def get_allflights_filtered(date=None, origin=None, destination=None, status=None):
    query = """
        SELECT
            f.Air_Craft_ID,
            f.Dep_Date,
            f.Dep_Hour,
            r.Origin,
            r.Destination,
            f.Arrival_Date,
            f.Arrival_Time,
            f.Economy_Price,
            f.Business_Price,
            f.Status
        FROM Flight f
        JOIN Route r ON f.Route_ID = r.Route_ID
        WHERE 1=1
    """
    params = []

    if date:
        query += " AND f.Dep_Date = %s"
        params.append(date)

    if origin:
        query += " AND r.Origin LIKE %s"
        params.append(f"%{origin}%")

    if destination:
        query += " AND r.Destination LIKE %s"
        params.append(f"%{destination}%")

    if status:
        query += " AND f.Status = %s"
        params.append(status)

    query += " ORDER BY f.Dep_Date, f.Dep_Hour"

    with db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()



def add_employee(id, fullname, phone, startdate, role, istrained, city, street, housenum):
    with db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM employee WHERE id = %s", (id,))
        result = cursor.fetchone()
        if result:
            return False

        if role == "crew":
            cursor.execute(
                "INSERT INTO employee(id, full_name_heb, phone_num, start_work_date, role) VALUES(%s, %s, %s, %s, %s)",
                (id, fullname, phone, startdate, "Flight_Attendant")
            )
            cursor.execute(
                "INSERT INTO flight_attendent(id, long_dist_training) VALUES(%s, %s)",
                (id, istrained)
            )
        elif role == "pilot":
            cursor.execute(
                "INSERT INTO employee(id, full_name_heb, phone_num, start_work_date, role) VALUES(%s, %s, %s, %s, %s)",
                (id, fullname, phone, startdate, "Pilot")
            )
            cursor.execute(
                "INSERT INTO pilot(id, long_dist_training) VALUES(%s, %s)",
                (id, istrained)
            )

        cursor.execute(
            "INSERT INTO address(id, city, street, house_num) VALUES(%s, %s, %s, %s)",
            (id, city, street, housenum)
        )
        return True

def check_aircraft(id):
    with db_cursor() as cursor:
        cursor.execute('SELECT 1 FROM Air_Craft WHERE Air_Craft_ID = %s LIMIT 1', (id,))
        result = cursor.fetchone()
        return result is not None

def validate_seats(rows, cols, max_rows, max_cols):
    if rows is None or cols is None:
        return False, "חסרים ערכים"
    try:
        rows = int(rows)
        cols = int(cols)
    except ValueError:
        return False, "ערכים לא מספריים"
    if rows < 1 or cols < 1:
        return False, "הערכים חייבים להיות חיוביים"
    if rows > max_rows or cols > max_cols:
        return False, f"מקסימום {max_rows} שורות ו-{max_cols} טורים"
    return True, (rows, cols)

def add_aircraft(aircraft, econrow, econcol, buiscol=None, buisrow=None):
    with db_cursor() as cursor:
        cursor.execute('INSERT INTO Air_Craft VALUES(%s, %s, %s, %s)',(aircraft[0],aircraft[2],aircraft[1],aircraft[3]))
        cursor.execute('INSERT INTO AirCraft_Class VALUES(%s,%s, %s, %s)',(aircraft[0],"Economy",econrow,econcol))
        if buiscol != None:
            cursor.execute('INSERT INTO AirCraft_Class VALUES(%s, %s, %s, %s)', (aircraft[0], "Business", buisrow, buiscol))



def get_origins():
    with db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT(origin) FROM route")
        return [row[0] for row in cursor.fetchall()]


def get_dest():
    with db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT(destination) FROM route")
        return [row[0] for row in cursor.fetchall()]



def calculate_arrival_datetime(dep_date, dep_hour, duration):
    return datetime.combine(dep_date, dep_hour) + timedelta(hours=duration)


def get_route_by_origin_dest(origin, destination):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT Route_ID, Duration FROM Route WHERE Origin=%s AND Destination=%s",
            (origin, destination)
        )
        return cursor.fetchone()

def get_specific_aricrafts(origin, dest, depdate, deptime):
    route = get_route_by_origin_dest(origin, dest)
    if isinstance(depdate, str):
        depdate = datetime.strptime(depdate, "%Y-%m-%d").date()
    if isinstance(deptime, str):
        fmt = "%H:%M:%S" if len(deptime) == 8 else "%H:%M"
        deptime = datetime.strptime(deptime, fmt).time()
    duration = float(route[1])
    dep_dt = datetime.combine(depdate, deptime)
    size_filter = " AND ac.Size = 'Large' " if duration > 6.0 else ""
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT DISTINCT ac.Air_Craft_ID, ac.Manufacturer, ac.Size
            FROM Air_Craft ac
            LEFT JOIN Flight f
              ON f.Air_Craft_ID = ac.Air_Craft_ID
            LEFT JOIN Route r
              ON r.Route_ID = f.Route_ID
            WHERE
              (
                f.Air_Craft_ID IS NULL
                OR (
                  TIMESTAMP(f.Arrival_Date, f.Arrival_Time) = (
                      SELECT MAX(TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time))
                      FROM Flight f2
                      WHERE f2.Air_Craft_ID = ac.Air_Craft_ID
                        AND TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time) <= %s
                  )
                  AND r.Destination = %s
                )
              )
              {size_filter}
            ORDER BY ac.Air_Craft_ID
            """,
            (dep_dt, origin)
        )
        return cursor.fetchall()



def getaircraft_byid(id):
    with db_cursor() as cursor:
        cursor.execute("SELECT Manufacturer, Size FROM Air_Craft WHERE Air_Craft_ID = %s", (id,))
        return cursor.fetchone()

def get_available_pilots(origin, depdate, deptime, is_long_flight):
    if isinstance(depdate, str):
        depdate = datetime.strptime(depdate, "%Y-%m-%d").date()
    if isinstance(deptime, str):
        fmt = "%H:%M:%S" if len(deptime) == 8 else "%H:%M"
        deptime = datetime.strptime(deptime, fmt).time()

    dep_dt = datetime.combine(depdate, deptime)

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT e.ID, e.Full_Name_Heb
            FROM Employee e
            JOIN Pilot p ON p.ID = e.ID
            WHERE
              (%s = 0 OR p.Long_Dist_Training = 1)
              AND (
                NOT EXISTS (
                  SELECT 1
                  FROM Flight_Crew fc0
                  WHERE fc0.ID = e.ID
                )
                OR
                EXISTS (
                  SELECT 1
                  FROM Flight_Crew fc1
                  JOIN Flight f1
                    ON f1.Air_Craft_ID = fc1.Air_Craft_ID
                   AND f1.Dep_Date    = fc1.Dep_Date
                   AND f1.Dep_Hour    = fc1.Dep_Hour
                  JOIN Route r1
                    ON r1.Route_ID = f1.Route_ID
                  WHERE fc1.ID = e.ID
                    AND TIMESTAMP(f1.Arrival_Date, f1.Arrival_Time) = (
                      SELECT MAX(TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time))
                      FROM Flight_Crew fc2
                      JOIN Flight f2
                        ON f2.Air_Craft_ID = fc2.Air_Craft_ID
                       AND f2.Dep_Date    = fc2.Dep_Date
                       AND f2.Dep_Hour    = fc2.Dep_Hour
                      WHERE fc2.ID = e.ID
                        AND TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time) <= %s
                    )
                    AND r1.Destination = %s
                )
              )
            ORDER BY e.Full_Name_Heb
            """,
            (1 if is_long_flight else 0, dep_dt, origin)
        )
        return cursor.fetchall()


def get_available_attendants(origin, depdate, deptime, is_long_flight):
    if isinstance(depdate, str):
        depdate = datetime.strptime(depdate, "%Y-%m-%d").date()
    if isinstance(deptime, str):
        fmt = "%H:%M:%S" if len(deptime) == 8 else "%H:%M"
        deptime = datetime.strptime(deptime, fmt).time()

    dep_dt = datetime.combine(depdate, deptime)

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT e.ID, e.Full_Name_Heb
            FROM Employee e
            JOIN Flight_attendent fa ON fa.ID = e.ID
            WHERE
              (%s = 0 OR fa.Long_Dist_Training = 1)
              AND (
                NOT EXISTS (
                  SELECT 1
                  FROM Flight_Crew fc0
                  WHERE fc0.ID = e.ID
                )
                OR
                EXISTS (
                  SELECT 1
                  FROM Flight_Crew fc1
                  JOIN Flight f1
                    ON f1.Air_Craft_ID = fc1.Air_Craft_ID
                   AND f1.Dep_Date    = fc1.Dep_Date
                   AND f1.Dep_Hour    = fc1.Dep_Hour
                  JOIN Route r1
                    ON r1.Route_ID = f1.Route_ID
                  WHERE fc1.ID = e.ID
                    AND TIMESTAMP(f1.Arrival_Date, f1.Arrival_Time) = (
                      SELECT MAX(TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time))
                      FROM Flight_Crew fc2
                      JOIN Flight f2
                        ON f2.Air_Craft_ID = fc2.Air_Craft_ID
                       AND f2.Dep_Date    = fc2.Dep_Date
                       AND f2.Dep_Hour    = fc2.Dep_Hour
                      WHERE fc2.ID = e.ID
                        AND TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time) <= %s
                    )
                    AND r1.Destination = %s
                )
              )
            ORDER BY e.Full_Name_Heb
            """,
            (1 if is_long_flight else 0, dep_dt, origin)
        )
        return cursor.fetchall()

def get_employee_names_by_ids(ids):
    if not ids:
        return []
    placeholders = ",".join(["%s"] * len(ids))
    with db_cursor() as cursor:
        cursor.execute(
            f"SELECT ID, Full_Name_Heb FROM Employee WHERE ID IN ({placeholders})",
            tuple(ids)
        )
        rows = cursor.fetchall()
    name_map = {r[0]: r[1] for r in rows}
    return [(i, name_map.get(i, "")) for i in ids]




def create_flight_and_assign_crew(
    aircraft_id,
    origin,
    dest,
    depdate,
    deptime,
    economy_price,
    business_price,
    pilot_ids,
    attendant_ids,
    status="Scheduled"
):
    if isinstance(depdate, str):
        dep_date = datetime.strptime(depdate, "%Y-%m-%d").date()
    else:
        dep_date = depdate
    if isinstance(deptime, str):
        fmt = "%H:%M:%S" if len(deptime) == 8 else "%H:%M"
        dep_time = datetime.strptime(deptime, fmt).time()
    else:
        dep_time = deptime
    route = get_route_by_origin_dest(origin, dest)   # (Route_ID, Duration)
    route_id = route[0]
    duration = float(route[1])
    dep_dt = datetime.combine(dep_date, dep_time)
    arr_dt = dep_dt + timedelta(hours=duration)
    arrival_date = arr_dt.date()
    arrival_time = arr_dt.time().replace(second=0, microsecond=0)

    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO Flight
            (Air_Craft_ID, Dep_Date, Dep_Hour, Route_ID,
             Arrival_Date, Arrival_Time,
             Economy_Price, Business_Price, Status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                aircraft_id,
                dep_date,
                dep_time,
                route_id,
                arrival_date,
                arrival_time,
                economy_price,
                business_price,
                status
            )
        )
        for pid in pilot_ids:
            cursor.execute(
                """
                INSERT INTO Flight_Crew
                (ID, Air_Craft_ID, Dep_Date, Dep_Hour, Role)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (pid, aircraft_id, dep_date, dep_time, "Pilot")
            )
        for aid in attendant_ids:
            cursor.execute(
                """
                INSERT INTO Flight_Crew
                (ID, Air_Craft_ID, Dep_Date, Dep_Hour, Role)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (aid, aircraft_id, dep_date, dep_time, "Flight_Attendant")
            )

    return True
