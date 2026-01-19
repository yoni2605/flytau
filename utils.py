import os
from contextlib import contextmanager
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime, timedelta, date, time
from decimal import Decimal, ROUND_HALF_UP
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

load_dotenv()

# ====== STATUS CONSTANTS (MUST MATCH DB ENUMS EXACTLY) ======
FLIGHT_STATUS_SCHEDULED = "SCHEDULED"
FLIGHT_STATUS_FULLY_BOOKED = "FULLY BOOKED"
FLIGHT_STATUS_COMPLETED = "COMPLETED"
FLIGHT_STATUS_CANCELED = "CANCELED"

ORDER_STATUS_ACTIVE = "Active"
ORDER_STATUS_COMPLETED = "Completed"
ORDER_STATUS_CUSTOMER_CANCELED = "Customer_Canceled"
ORDER_STATUS_SYSTEM_CANCELED = "System_Canceled"


def normalize_flight_status(s: str) -> str:
    """
    Normalize various UI/code spellings to DB enum values.
    Keeps your app safe if somewhere you pass "Scheduled"/"Canceled"/etc.
    """
    if s is None:
        return FLIGHT_STATUS_SCHEDULED
    s0 = str(s).strip()
    if s0 in (FLIGHT_STATUS_SCHEDULED, FLIGHT_STATUS_FULLY_BOOKED, FLIGHT_STATUS_COMPLETED, FLIGHT_STATUS_CANCELED):
        return s0

    low = s0.lower().replace("_", " ").strip()
    mapping = {
        "scheduled": FLIGHT_STATUS_SCHEDULED,
        "fully booked": FLIGHT_STATUS_FULLY_BOOKED,
        "full": FLIGHT_STATUS_FULLY_BOOKED,
        "completed": FLIGHT_STATUS_COMPLETED,
        "canceled": FLIGHT_STATUS_CANCELED,
        "cancelled": FLIGHT_STATUS_CANCELED,
        "canceled ": FLIGHT_STATUS_CANCELED,
        "cancelled ": FLIGHT_STATUS_CANCELED,
    }
    return mapping.get(low, FLIGHT_STATUS_SCHEDULED)


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=True,
        connection_timeout=5,
    )


# מנהל הקשר שמספק מצביע למסד נתונים ומבצע שמירה וסגירה אוטומטית של החיבור
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


# time to timedelta
def timedelta_to_time(td: timedelta) -> time:
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return time(hour=hours, minute=minutes, second=seconds)


# ממיר ערך זמן שמגיע מהמסד לאובייקט זמן
def mysql_time_to_time(t):
    if isinstance(t, time):
        return t.replace(microsecond=0)
    if isinstance(t, timedelta):
        return timedelta_to_time(t).replace(microsecond=0)
    raise TypeError(f"Unsupported TIME type from DB: {type(t)}")


# יוצר משתמש חדש ומוסיף את המידע שלו לטבלאות הלקוח והטלפונים
def new_user(fullname, email, password, passport, dob, signup_date, phones):
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO customer(Email, Full_Name_Eng) VALUES (%s, %s)",
            (email, fullname),
        )
        cursor.execute(
            "INSERT INTO registered_customer(Email, Passport_Num, Birth_Date, Joining_Date, Password) "
            "VALUES (%s, %s, %s, %s, %s)",
            (email, passport, dob, signup_date, password),
        )
        for phone in phones:
            cursor.execute(
                "INSERT INTO phone_numbers(Cust_Email, Phone_num) VALUES(%s, %s)",
                (email, phone),
            )


# בודק אם כתובת מייל כבר קיימת במסד
def mailexists(mail):
    with db_cursor() as cursor:
        cursor.execute("SELECT Email FROM customer")
        allmails = [row[0] for row in cursor.fetchall()]
        return str(mail) in allmails


# בודק אם לקוח עם מייל וסיסמה קיימים במסד
def checkcust(mail, password):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM registered_customer WHERE Email = %s AND Password = %s",
            (mail, password),
        )
        return cursor.fetchone() is not None


# מחזיר את השם המלא של הלקוח לפי מייל
def getname(mail):
    with db_cursor() as cursor:
        cursor.execute("SELECT Full_Name_Eng FROM customer WHERE Email = %s", (mail,))
        result = cursor.fetchone()
    return result[0] if result else None


# בודק אם מנהל עם מזהה וסיסמה קיימים במסד
def checkmgr(id, password):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM manager WHERE ID = %s AND Login_pass = %s",
            (id, password),
        )
        return cursor.fetchone() is not None


# מחזיר את השם המלא של המנהל לפי מזהה
def getmgr(id):
    with db_cursor() as cursor:
        cursor.execute("SELECT Full_Name_Heb FROM employee WHERE ID = %s", (id,))
        result = cursor.fetchone()
    return result[0] if result else None


# בודק אם השם כתוב בעברית בלבד
def is_hebrew_name(name):
    for char in name:
        if not ("א" <= char <= "ת" or char == " "):
            return False
    return True


# מחזיר את כל הטיסות עם אפשרות לסינון לפי תאריך, מקור, יעד או סטטוס
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
        FROM flight f
        JOIN route r ON f.Route_ID = r.Route_ID
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
        params.append(normalize_flight_status(status))
    query += " ORDER BY TIMESTAMP(f.Dep_Date, f.Dep_Hour) ASC"

    with db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        return cursor.fetchall()


# הוספת עובדים למערכת
def add_employee(id, fullname, phone, startdate, role, istrained, city, street, housenum):
    with db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM employee WHERE ID = %s", (id,))
        if cursor.fetchone():
            return False

        if role == "crew":
            cursor.execute(
                "INSERT INTO employee(ID, Full_Name_Heb, Phone_num, Start_Work_Date, Role) "
                "VALUES(%s, %s, %s, %s, %s)",
                (id, fullname, phone, startdate, "Flight_Attendant"),
            )
            cursor.execute(
                "INSERT INTO flight_attendent(ID, Long_Dist_Training) VALUES(%s, %s)",
                (id, istrained),
            )
        elif role == "pilot":
            cursor.execute(
                "INSERT INTO employee(ID, Full_Name_Heb, Phone_num, Start_Work_Date, Role) "
                "VALUES(%s, %s, %s, %s, %s)",
                (id, fullname, phone, startdate, "Pilot"),
            )
            cursor.execute(
                "INSERT INTO pilot(ID, Long_Dist_Training) VALUES(%s, %s)",
                (id, istrained),
            )

        cursor.execute(
            "INSERT INTO address(ID, City, Street, House_num) VALUES(%s, %s, %s, %s)",
            (id, city, street, housenum),
        )
        return True


# בודק אם מטוס עם מזהה נתון קיים במסד
def check_aircraft(id):
    with db_cursor() as cursor:
        cursor.execute("SELECT 1 FROM air_craft WHERE Air_Craft_ID = %s LIMIT 1", (id,))
        return cursor.fetchone() is not None


# בודק אם מספר שורות וטורים תקינים במסגרת המקסימום
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


# הוספת מטוס לבסיס הנתונים
def add_aircraft(aircraft, econrow, econcol, buiscol=None, buisrow=None):
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO air_craft (Air_Craft_ID, Purchase_Date, Manufacturer, Size) VALUES(%s, %s, %s, %s)",
            (aircraft[0], aircraft[2], aircraft[1], aircraft[3]),
        )
        cursor.execute(
            "INSERT INTO aircraft_class (Air_Craft_ID, Class, Row_Num, Col_Num) VALUES(%s, %s, %s, %s)",
            (aircraft[0], "Economy", econrow, econcol),
        )
        if buiscol is not None:
            cursor.execute(
                "INSERT INTO aircraft_class (Air_Craft_ID, Class, Row_Num, Col_Num) VALUES(%s, %s, %s, %s)",
                (aircraft[0], "Business", buisrow, buiscol),
            )


# מחזיר את כל שדות המוצא השונים מהטבלה
def get_origins():
    with db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT Origin FROM route")
        return [row[0] for row in cursor.fetchall()]


# מחזיר את כל היעדים השונים מהטבלה
def get_dest():
    with db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT Destination FROM route")
        return [row[0] for row in cursor.fetchall()]


# חישוב זמן הגעה לפי משך טיסה זמן המראה תאריך המראה
def calculate_arrival_datetime(dep_date, dep_hour, duration):
    return datetime.combine(dep_date, dep_hour) + timedelta(hours=duration)


# מחזיר את הנתיב והמשך הטיסה לפי מקור ויעד
def get_route_by_origin_dest(origin, destination):
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT Route_ID, Duration FROM route WHERE Origin=%s AND Destination=%s",
            (origin, destination),
        )
        return cursor.fetchone()


# מחזיר מטוסים זמינים לטיסה מסוימת לפי מקור, יעד, תאריך ושעה
def get_specific_aricrafts(origin, dest, depdate, deptime):
    route = get_route_by_origin_dest(origin, dest)
    if not route:
        return []

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
            FROM air_craft ac
            LEFT JOIN flight f
              ON f.Air_Craft_ID = ac.Air_Craft_ID
            LEFT JOIN route r
              ON r.Route_ID = f.Route_ID
            WHERE
              (
                f.Air_Craft_ID IS NULL
                OR (
                  TIMESTAMP(f.Arrival_Date, f.Arrival_Time) = (
                      SELECT MAX(TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time))
                      FROM flight f2
                      WHERE f2.Air_Craft_ID = ac.Air_Craft_ID
                        AND TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time) <= %s
                  )
                  AND r.Destination = %s
                )
              )
              {size_filter}
            ORDER BY ac.Air_Craft_ID
            """,
            (dep_dt, origin),
        )
        return cursor.fetchall()


# מחזיר יצרן וגודל של מטוס לפי מזהה
def getaircraft_byid(id):
    with db_cursor() as cursor:
        cursor.execute("SELECT Manufacturer, Size FROM air_craft WHERE Air_Craft_ID = %s", (id,))
        return cursor.fetchone()


# מחזיר טייסים זמינים לטיסה לפי תאריך, שעה ומרחק הטיסה
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
            FROM employee e
            JOIN pilot p ON p.ID = e.ID
            WHERE
              (%s = 0 OR p.Long_Dist_Training = 1)
              AND (
                NOT EXISTS (
                  SELECT 1
                  FROM flight_crew fc0
                  WHERE fc0.ID = e.ID
                )
                OR
                EXISTS (
                  SELECT 1
                  FROM flight_crew fc1
                  JOIN flight f1
                    ON f1.Air_Craft_ID = fc1.Air_Craft_ID
                   AND f1.Dep_Date    = fc1.Dep_Date
                   AND f1.Dep_Hour    = fc1.Dep_Hour
                  JOIN route r1
                    ON r1.Route_ID = f1.Route_ID
                  WHERE fc1.ID = e.ID
                    AND TIMESTAMP(f1.Arrival_Date, f1.Arrival_Time) = (
                      SELECT MAX(TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time))
                      FROM flight_crew fc2
                      JOIN flight f2
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
            (1 if is_long_flight else 0, dep_dt, origin),
        )
        return cursor.fetchall()


# מחזיר דיילים זמינים לטיסה לפי תאריך, שעה ומרחק הטיסה
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
            FROM employee e
            JOIN flight_attendent fa ON fa.ID = e.ID
            WHERE
              (%s = 0 OR fa.Long_Dist_Training = 1)
              AND (
                NOT EXISTS (
                  SELECT 1
                  FROM flight_crew fc0
                  WHERE fc0.ID = e.ID
                )
                OR
                EXISTS (
                  SELECT 1
                  FROM flight_crew fc1
                  JOIN flight f1
                    ON f1.Air_Craft_ID = fc1.Air_Craft_ID
                   AND f1.Dep_Date    = fc1.Dep_Date
                   AND f1.Dep_Hour    = fc1.Dep_Hour
                  JOIN route r1
                    ON r1.Route_ID = f1.Route_ID
                  WHERE fc1.ID = e.ID
                    AND TIMESTAMP(f1.Arrival_Date, f1.Arrival_Time) = (
                      SELECT MAX(TIMESTAMP(f2.Arrival_Date, f2.Arrival_Time))
                      FROM flight_crew fc2
                      JOIN flight f2
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
            (1 if is_long_flight else 0, dep_dt, origin),
        )
        return cursor.fetchall()


# מחזיר שמות עובדים לפי רשימת מזהים
def get_employee_names_by_ids(ids):
    if not ids:
        return []
    placeholders = ",".join(["%s"] * len(ids))
    with db_cursor() as cursor:
        cursor.execute(
            f"SELECT ID, Full_Name_Heb FROM employee WHERE ID IN ({placeholders})",
            tuple(ids),
        )
        rows = cursor.fetchall()
    name_map = {r[0]: r[1] for r in rows}
    return [(i, name_map.get(i, "")) for i in ids]


# יוצר טיסה ומקצה לה צוות טייסים ודיילים
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
    status=FLIGHT_STATUS_SCHEDULED,
):
    status = normalize_flight_status(status)

    if isinstance(depdate, str):
        dep_date = datetime.strptime(depdate, "%Y-%m-%d").date()
    else:
        dep_date = depdate

    if isinstance(deptime, str):
        fmt = "%H:%M:%S" if len(deptime) == 8 else "%H:%M"
        dep_time = datetime.strptime(deptime, fmt).time()
    else:
        dep_time = deptime

    route = get_route_by_origin_dest(origin, dest)
    if not route:
        return False

    route_id = route[0]
    duration = float(route[1])

    dep_dt = datetime.combine(dep_date, dep_time)
    arr_dt = dep_dt + timedelta(hours=duration)
    arrival_date = arr_dt.date()
    arrival_time = arr_dt.time().replace(second=0, microsecond=0)

    with db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO flight
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
                status,
            ),
        )

        for pid in pilot_ids:
            cursor.execute(
                """
                INSERT INTO flight_crew
                (ID, Air_Craft_ID, Dep_Date, Dep_Hour, Role)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (pid, aircraft_id, dep_date, dep_time, "Pilot"),
            )
        for aid in attendant_ids:
            cursor.execute(
                """
                INSERT INTO flight_crew
                (ID, Air_Craft_ID, Dep_Date, Dep_Hour, Role)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (aid, aircraft_id, dep_date, dep_time, "Flight_Attendant"),
            )
    return True


# ביטול טיסה במסגרת הגבלות כולל בדיקות
def cancel_flight_if_allowed(aircraft_id: str, dep_date: date, dep_time: time, origin: str, destination: str):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "SELECT Route_ID FROM route WHERE Origin=%s AND Destination=%s",
            (origin, destination),
        )
        r = cur.fetchone()
        if not r:
            return False, "הנתיב לא נמצא"
        route_id = r[0]

        cur.execute(
            """
            SELECT Status, Dep_Date, Dep_Hour
            FROM flight
            WHERE Air_Craft_ID=%s
              AND Dep_Date=%s
              AND Dep_Hour=%s
              AND Route_ID=%s
            """,
            (aircraft_id, dep_date, dep_time, route_id),
        )
        row = cur.fetchone()
        if not row:
            return False, "הטיסה לא נמצאה"

        status, db_dep_date, db_dep_time = row
        status = normalize_flight_status(status)
        if status == FLIGHT_STATUS_CANCELED:
            return False, "הטיסה כבר בוטלה"

        dep_time_fixed = mysql_time_to_time(db_dep_time)
        dep_dt = datetime.combine(db_dep_date, dep_time_fixed)

        if dep_dt - datetime.now() <= timedelta(hours=72):
            return False, "לא ניתן לבטל טיסה פחות מ־72 שעות לפני ההמראה"

        cur.execute(
            """
            UPDATE flight
            SET Status=%s
            WHERE Air_Craft_ID=%s
              AND Dep_Date=%s
              AND Dep_Hour=%s
              AND Route_ID=%s
            """,
            (FLIGHT_STATUS_CANCELED, aircraft_id, dep_date, dep_time, route_id),
        )

        cur.execute(
            """
            SELECT DISTINCT Order_ID
            FROM tickets
            WHERE Air_Craft_ID=%s
              AND Dep_Date=%s
              AND Dep_Hour=%s
            """,
            (aircraft_id, dep_date, dep_time),
        )
        orders = [row[0] for row in cur.fetchall()]
        if orders:
            format_strings = ",".join(["%s"] * len(orders))
            cur.execute(
                f"""
                UPDATE flight_order
                SET Order_status=%s, Total_Paid=0
                WHERE Order_ID IN ({format_strings})
                """,
                tuple([ORDER_STATUS_SYSTEM_CANCELED] + orders),
            )

        db.commit()
        return True, "הטיסה בוטלה בהצלחה"
    finally:
        cur.close()
        db.close()


# מחזיר את מספר השורות והטורים של מחלקת מושבים במטוס
def get_class_layout(aircraft_id, seat_class):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT Row_Num, Col_Num
            FROM aircraft_class
            WHERE Air_Craft_ID = %s AND Class = %s
            """,
            (aircraft_id, seat_class),
        )
        row = cursor.fetchone()
    if row is None:
        raise ValueError(f"No layout found for aircraft {aircraft_id} and class {seat_class}")
    return int(row[0]), int(row[1])


# מחזיר את כל המושבים שכבר תפוסים בטיסה מסוימת
def get_taken_seat_for_flight(aircraft_id, dep_date, dep_hour):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT t.Chosen_Row_Num, t.Chosen_Col_Num
            FROM tickets t
            JOIN flight_order fo
              ON fo.Order_ID = t.Order_ID
            WHERE t.Air_Craft_ID = %s
              AND t.Dep_Date = DATE(%s)
              AND t.Dep_Hour = TIME(%s)
              AND fo.Order_status = %s
            """,
            (aircraft_id, dep_date, dep_hour, ORDER_STATUS_ACTIVE),
        )
        rows = cursor.fetchall()
    return {f"{int(r)}:{int(c)}" for (r, c) in rows}


# מחזיר את כל הטיסות שלא בוטלו עם פרטי הטיסה
def get_all_flights_not_cancelled():
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                f.Air_Craft_ID,
                f.Route_ID,
                f.Dep_Date,
                f.Dep_Hour,
                r.Duration,
                f.Status
            FROM flight f
            JOIN route r ON r.Route_ID = f.Route_ID
            WHERE f.Status <> %s
            """,
            (FLIGHT_STATUS_CANCELED,),
        )
        rows = cursor.fetchall()

    flights = []
    for air, route_id, dep_date, dep_hour, duration, status in rows:
        flights.append(
            {
                "aircraft": air,
                "route_id": route_id,
                "dep_date": dep_date,
                "dep_time": mysql_time_to_time(dep_hour),
                "duration": float(duration),
                "status": normalize_flight_status(status),
            }
        )
    return flights


# פונקציית עזר לפונקציית ()update_flight_status שמקבלת פרטי טיסה ספציפית ומעדכנת אותם
def update_flight_status(aircraft, route_id, dep_date, dep_time, new_status):
    new_status = normalize_flight_status(new_status)
    with db_cursor() as cursor:
        cursor.execute(
            """
            UPDATE flight
            SET Status = %s
            WHERE Air_Craft_ID = %s
              AND Route_ID = %s
              AND Dep_Date = %s
              AND Dep_Hour = %s
            """,
            (new_status, aircraft, route_id, dep_date, dep_time),
        )


# עדכון סטטוס טיסה
def update_flights_status():
    now = datetime.now()
    flights = get_all_flights_not_cancelled()
    for f in flights:
        if f["status"] == FLIGHT_STATUS_CANCELED:
            continue
        dep_dt = datetime.combine(f["dep_date"], f["dep_time"])
        landing_dt = dep_dt + timedelta(hours=f["duration"])
        if now >= landing_dt and f["status"] != FLIGHT_STATUS_COMPLETED:
            update_flight_status(
                f["aircraft"],
                f["route_id"],
                f["dep_date"],
                f["dep_time"],
                FLIGHT_STATUS_COMPLETED,
            )


# מוסיף אורח לבסיס נתונים
def new_guest(email, fullname, phones):
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO customer(Email, Full_Name_Eng) VALUES (%s, %s)",
            (email, fullname),
        )
        for phone in phones:
            cursor.execute(
                "INSERT INTO phone_numbers(Cust_Email, Phone_num) VALUES(%s, %s)",
                (email, phone),
            )


# יוצר הזמנה ומכניס את כרטיסי הנוסעים עם מחירים מתאימים
def insert_order_and_tickets(email, aircraft_id, dep_date, dep_hour, econ_seats, busi_seats, econ_price, busi_price, total_paid):
    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO flight_order (Email, Order_Date, Order_status, Total_Paid) VALUES (%s, CURDATE(), %s, %s)",
            (email, ORDER_STATUS_ACTIVE, total_paid),
        )
        order_id = cursor.lastrowid

        for seat in econ_seats:
            row, col = seat.split("-")
            cursor.execute(
                """
                INSERT INTO tickets
                (Order_ID, Air_Craft_ID, Dep_Date, Dep_Hour, Chosen_Row_Num, Chosen_Col_Num, Price_Paid)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (order_id, aircraft_id, dep_date, dep_hour, int(row), int(col), econ_price),
            )

        for seat in busi_seats:
            row, col = seat.split("-")
            cursor.execute(
                """
                INSERT INTO tickets
                (Order_ID, Air_Craft_ID, Dep_Date, Dep_Hour, Chosen_Row_Num, Chosen_Col_Num, Price_Paid)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (order_id, aircraft_id, dep_date, dep_hour, int(row), int(col), busi_price),
            )

        return order_id


# שינוי סטטוס לתפוסה מלאה
def update_flights_fully_booked():
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE flight f
            JOIN (
                SELECT
                    f2.Air_Craft_ID,
                    f2.Dep_Date,
                    f2.Dep_Hour,
                    (
                        SELECT COALESCE(SUM(acc.Row_Num * acc.Col_Num), 0)
                        FROM aircraft_class acc
                        WHERE acc.Air_Craft_ID = f2.Air_Craft_ID
                    ) AS capacity,
                    (
                        SELECT COUNT(*)
                        FROM tickets t
                        WHERE t.Air_Craft_ID = f2.Air_Craft_ID
                          AND t.Dep_Date    = f2.Dep_Date
                          AND t.Dep_Hour    = f2.Dep_Hour
                    ) AS total_tickets,
                    (
                        SELECT COUNT(*)
                        FROM tickets t
                        JOIN flight_order fo ON fo.Order_ID = t.Order_ID
                        WHERE t.Air_Craft_ID = f2.Air_Craft_ID
                          AND t.Dep_Date    = f2.Dep_Date
                          AND t.Dep_Hour    = f2.Dep_Hour
                          AND fo.Order_status = '{ORDER_STATUS_ACTIVE}'
                    ) AS active_tickets
                FROM flight f2
                WHERE f2.Status NOT IN ('{FLIGHT_STATUS_CANCELED}', '{FLIGHT_STATUS_COMPLETED}', '{FLIGHT_STATUS_FULLY_BOOKED}')
            ) x
              ON x.Air_Craft_ID = f.Air_Craft_ID
             AND x.Dep_Date     = f.Dep_Date
             AND x.Dep_Hour     = f.Dep_Hour
            SET f.Status = '{FLIGHT_STATUS_FULLY_BOOKED}'
            WHERE x.capacity > 0
              AND x.total_tickets = x.capacity
              AND x.active_tickets = x.total_tickets
              AND f.Status NOT IN ('{FLIGHT_STATUS_CANCELED}', '{FLIGHT_STATUS_COMPLETED}', '{FLIGHT_STATUS_FULLY_BOOKED}')
            """
        )


# מחזיר הזמנה עם כל הכרטיסים והפרטים שלהם לפי מזהה מייל והזמנה
def get_order_with_tickets(order_id: int, email: str):
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT
                fo.Order_ID,
                fo.Email,
                fo.Order_Date,
                fo.Order_status,
                fo.Total_Paid
            FROM flight_order fo
            WHERE fo.Order_ID = %s AND fo.Email = %s
            """,
            (order_id, email),
        )
        order = cursor.fetchone()
        if not order:
            raise ValueError("Order not found for this email")

        cursor.execute(
            """
            SELECT
                t.Order_ID, t.Air_Craft_ID, t.Dep_Date, t.Dep_Hour, t.Chosen_Row_Num, t.Chosen_Col_Num, t.Price_Paid,
                f.Route_ID, f.Arrival_Date, f.Arrival_Time, f.Status AS Flight_Status,
                r.Origin, r.Destination, r.Duration
            FROM tickets t
            LEFT JOIN flight f
              ON f.Air_Craft_ID = t.Air_Craft_ID
             AND f.Dep_Date = t.Dep_Date
             AND f.Dep_Hour = t.Dep_Hour
            LEFT JOIN route r
              ON r.Route_ID = f.Route_ID
            WHERE t.Order_ID = %s
            ORDER BY t.Dep_Date, t.Dep_Hour, t.Chosen_Row_Num, t.Chosen_Col_Num
            """,
            (order_id,),
        )
        tickets = cursor.fetchall()

    for tk in tickets:
        if tk.get("Dep_Hour") is not None:
            tk["Dep_Hour"] = mysql_time_to_time(tk["Dep_Hour"])
        if tk.get("Arrival_Time") is not None:
            tk["Arrival_Time"] = mysql_time_to_time(tk["Arrival_Time"])
        if tk.get("Flight_Status") is not None:
            tk["Flight_Status"] = normalize_flight_status(tk["Flight_Status"])
    return order, tickets


# בדיקה אם הזמנה קיימת לפי מייל ומזהה הזמנה
def order_exists_for_email(order_id: int, email: str):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM flight_order
            WHERE Order_ID = %s AND Email = %s
            LIMIT 1
            """,
            (order_id, email),
        )
        return cursor.fetchone() is not None


# ביטול טיסה לפי פרמטרים
def cancel_order_by_policy(order_id: int, email: str):
    with db_cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT Order_ID, Email, Order_status, Total_Paid
            FROM flight_order
            WHERE Order_ID=%s AND Email=%s
            """,
            (order_id, email),
        )
        order = cursor.fetchone()
        if not order:
            return False, "הזמנה לא נמצאה עבור המייל שסופק"
        if order["Order_status"] != ORDER_STATUS_ACTIVE:
            return False, "אפשר לבטל רק הזמנות פעילות (Active)"

        cursor.execute(
            """
            SELECT MIN(TIMESTAMP(t.Dep_Date, t.Dep_Hour)) AS nearest_dep
            FROM tickets t
            WHERE t.Order_ID = %s
            """,
            (order_id,),
        )
        row = cursor.fetchone()
        nearest_dep = row["nearest_dep"]
        if nearest_dep is None:
            return False, "אין כרטיסים להזמנה זו ולכן אין מה לבטל"

        cursor.execute("SELECT TIMESTAMPDIFF(HOUR, NOW(), %s) AS hours_left", (nearest_dep,))
        hours_left = cursor.fetchone()["hours_left"]
        if hours_left is None or hours_left <= 36:
            return False, "לא ניתן לבטל הזמנה 36 שעות (או פחות) לפני הטיסה"

        total_paid = Decimal(str(order["Total_Paid"]))
        new_total = (total_paid * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        cursor.execute(
            """
            UPDATE flight_order
            SET Order_status = %s,
                Total_Paid   = %s
            WHERE Order_ID = %s AND Email = %s
            """,
            (ORDER_STATUS_CUSTOMER_CANCELED, str(new_total), order_id, email),
        )
        return True, f"ההזמנה בוטלה בהצלחה. נגבתה עמלה של 5% והסכום עודכן ל-₪{new_total}."


# מחזיר את כל ההזמנות של לקוח רשום
def get_custorders(email: str, status_filter=None):
    with db_cursor(dictionary=True) as cursor:
        if status_filter:
            cursor.execute(
                """
                SELECT o.Order_ID, o.Email, o.Order_Date, o.Order_status, o.Total_Paid
                FROM flight_order o
                JOIN tickets t ON t.Order_ID = o.Order_ID
                WHERE o.Email = %s AND o.Order_status = %s
                ORDER BY t.Dep_Date ASC, t.Dep_Hour ASC
                """,
                (email, status_filter),
            )
        else:
            cursor.execute(
                """
                SELECT o.Order_ID, o.Email, o.Order_Date, o.Order_status, o.Total_Paid
                FROM flight_order o
                JOIN tickets t ON t.Order_ID = o.Order_ID
                WHERE o.Email = %s
                ORDER BY t.Dep_Date ASC, t.Dep_Hour ASC
                """,
                (email,),
            )
        orders = cursor.fetchall()

        for order in orders:
            cursor.execute(
                """
                SELECT
                    t.Order_ID, t.Air_Craft_ID, t.Dep_Date, t.Dep_Hour,
                    t.Chosen_Row_Num, t.Chosen_Col_Num, t.Price_Paid,
                    f.Status AS Flight_Status, f.Arrival_Date, f.Arrival_Time,
                    r.Origin, r.Destination
                FROM tickets t
                JOIN flight f
                  ON t.Air_Craft_ID = f.Air_Craft_ID
                 AND t.Dep_Date = f.Dep_Date
                 AND t.Dep_Hour = f.Dep_Hour
                JOIN route r
                  ON f.Route_ID = r.Route_ID
                WHERE t.Order_ID = %s
                ORDER BY t.Dep_Date, t.Dep_Hour, t.Chosen_Row_Num, t.Chosen_Col_Num
                """,
                (order["Order_ID"],),
            )
            order["tickets"] = cursor.fetchall()
        return orders


# מוודא שקיימת תיקיית דוחות ומחזיר את הנתיב שלה
def ensure_reports_dir(app) -> str:
    reports_dir = os.path.join(app.static_folder, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


# יוצר גרף קצב ביטולים לפי חודש ושומר אותו כקובץ
def make_cancel_rate_chart(rows, out_path: str):
    labels = [f"{r['y']}-{int(r['m']):02d}" for r in rows]
    values = [float(r["cancel_rate"]) for r in rows]
    plt.figure(figsize=(9, 3.2))
    plt.plot(labels, values, marker="o")
    plt.title("Cancel Rate by Month (%)")
    plt.xlabel("Month")
    plt.ylabel("Cancel Rate (%)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


# יוצר גרף עמודות של המסלולים עם ההכנסות הגבוהות ביותר
def make_revenue_routes_chart(rows, out_path: str):
    labels = [f"{r['Origin']} - {r['Destination']}" for r in rows]
    values = [float(r["revenue"]) for r in rows]
    plt.figure(figsize=(9, 3.6))
    plt.bar(labels, values)
    plt.title("Top Revenue Routes (Last 90 Days)")
    plt.xlabel("Route")
    plt.ylabel("Revenue")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


# החזרה של דוחות מנהלים
def get_manager_reports(app):
    queries = {
        "kpis": f"""
            SELECT
                SUM(CASE WHEN f.Dep_Date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
                          AND f.Dep_Date < DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH)
                          AND f.Status = '{FLIGHT_STATUS_SCHEDULED}' THEN 1 ELSE 0 END) AS scheduled_cnt,
                SUM(CASE WHEN f.Dep_Date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
                          AND f.Dep_Date < DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH)
                          AND f.Status = '{FLIGHT_STATUS_FULLY_BOOKED}' THEN 1 ELSE 0 END) AS full_cnt,
                SUM(CASE WHEN f.Dep_Date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
                          AND f.Dep_Date < DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH)
                          AND f.Status = '{FLIGHT_STATUS_COMPLETED}' THEN 1 ELSE 0 END) AS completed_cnt,
                SUM(CASE WHEN f.Dep_Date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
                          AND f.Dep_Date < DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH)
                          AND f.Status = '{FLIGHT_STATUS_CANCELED}' THEN 1 ELSE 0 END) AS cancelled_cnt
            FROM flight f;
        """,
        "cancel_rate": """
            SELECT YEAR(Order_Date) AS y, MONTH(Order_Date) AS m,
                   ROUND((SUM(CASE WHEN Order_status = 'Customer_Canceled' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS cancel_rate
            FROM flight_order
            GROUP BY YEAR(Order_Date), MONTH(Order_Date)
            ORDER BY y, m;
        """,
        "top_routes": f"""
            SELECT r.Origin, r.Destination, COUNT(*) AS completed_flights
            FROM flight f
            JOIN route r ON r.Route_ID = f.Route_ID
            WHERE f.Status = '{FLIGHT_STATUS_COMPLETED}'
              AND f.Dep_Date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY r.Origin, r.Destination
            ORDER BY completed_flights DESC
            LIMIT 10;
        """,
        "crew_load": f"""
            SELECT fc.ID AS employee_id,
                   SUM(CASE WHEN r.Duration > 6 THEN r.Duration ELSE 0 END) AS long_hours,
                   SUM(CASE WHEN r.Duration <= 6 THEN r.Duration ELSE 0 END) AS short_hours,
                   ROUND(SUM(r.Duration), 2) AS total_hours
            FROM flight_crew fc
            JOIN flight f ON f.Air_Craft_ID = fc.Air_Craft_ID
                          AND f.Dep_Date = fc.Dep_Date
                          AND f.Dep_Hour = fc.Dep_Hour
            JOIN route r ON r.Route_ID = f.Route_ID
            WHERE f.Status = '{FLIGHT_STATUS_COMPLETED}'
              AND f.Dep_Date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY fc.ID
            ORDER BY total_hours DESC
            LIMIT 20;
        """,
        "revenue_routes": f"""
            SELECT r.Origin, r.Destination,
                   ROUND(SUM(COALESCE(t.Price_Paid, 0)), 2) AS revenue,
                   COUNT(*) AS tickets_sold
            FROM tickets t
            JOIN flight f ON t.Air_Craft_ID = f.Air_Craft_ID
                          AND t.Dep_Date = f.Dep_Date
                          AND t.Dep_Hour = f.Dep_Hour
            JOIN route r ON r.Route_ID = f.Route_ID
            WHERE f.Status = '{FLIGHT_STATUS_COMPLETED}'
              AND f.Dep_Date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            GROUP BY r.Origin, r.Destination
            ORDER BY revenue DESC
            LIMIT 10;
        """,
    }

    results = {}
    with db_cursor() as cursor:
        for key, query in queries.items():
            cursor.execute(query)
            rows = cursor.fetchall()
            if key == "kpis":
                kpi_row = rows[0] if rows else (0, 0, 0, 0)
                results[key] = {
                    "scheduled_cnt": kpi_row[0] or 0,
                    "full_cnt": kpi_row[1] or 0,
                    "completed_cnt": kpi_row[2] or 0,
                    "cancelled_cnt": kpi_row[3] or 0,
                }
            elif key == "cancel_rate":
                results[key] = [{"y": r[0], "m": r[1], "cancel_rate": r[2]} for r in rows]
            elif key == "top_routes":
                results[key] = [{"Origin": r[0], "Destination": r[1], "completed_flights": r[2]} for r in rows]
            elif key == "crew_load":
                results[key] = [
                    {"employee_id": r[0], "long_hours": r[1], "short_hours": r[2], "total_hours": r[3]} for r in rows
                ]
            elif key == "revenue_routes":
                results[key] = [{"Origin": r[0], "Destination": r[1], "revenue": r[2], "tickets_sold": r[3]} for r in rows]
    return results


# מעדכן סטטוס טיסה
def update_orders_status_when_flight_completed():
    query = f"""
        UPDATE flight_order fo
        JOIN tickets t
          ON t.Order_ID = fo.Order_ID
        JOIN flight f
          ON f.Air_Craft_ID = t.Air_Craft_ID
         AND f.Dep_Date     = t.Dep_Date
         AND f.Dep_Hour     = t.Dep_Hour
        SET fo.Order_status = '{ORDER_STATUS_COMPLETED}'
        WHERE f.Status = '{FLIGHT_STATUS_COMPLETED}'
          AND fo.Order_status = '{ORDER_STATUS_ACTIVE}'
    """
    with db_cursor() as cur:
        cur.execute(query)


# שליפת פרטים של לקוח רשום בסיכום הזמנה
def get_passport_and_birthdate_by_email(email):
    query = """
        SELECT Passport_Num, Birth_Date
        FROM registered_customer
        WHERE Email = %s
    """
    with db_cursor(dictionary=True) as cur:
        cur.execute(query, (email,))
        return cur.fetchone()
