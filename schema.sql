
SET FOREIGN_KEY_CHECKS = 0;


DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS flight_order;
DROP TABLE IF EXISTS flight_crew;
DROP TABLE IF EXISTS flight;
DROP TABLE IF EXISTS aircraft_class;
DROP TABLE IF EXISTS air_craft;
DROP TABLE IF EXISTS phone_numbers;
DROP TABLE IF EXISTS registered_customer;
DROP TABLE IF EXISTS manager;
DROP TABLE IF EXISTS flight_attendent;
DROP TABLE IF EXISTS pilot;
DROP TABLE IF EXISTS address;
DROP TABLE IF EXISTS employee;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS route;

SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------------------------
-- Table structure
-- --------------------------------------------------------------------

CREATE TABLE route (
  Route_ID INT NOT NULL AUTO_INCREMENT,
  Origin VARCHAR(50) NOT NULL,
  Destination VARCHAR(50) NOT NULL,
  Duration DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (Route_ID),
  UNIQUE KEY Origin (Origin, Destination)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE customer (
  Email VARCHAR(100) NOT NULL,
  Full_Name_Eng VARCHAR(100) NOT NULL,
  PRIMARY KEY (Email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE employee (
  ID VARCHAR(20) NOT NULL,
  Full_Name_Heb VARCHAR(100) NOT NULL,
  Phone_num VARCHAR(20) DEFAULT NULL,
  Start_Work_Date DATE NOT NULL,
  Role ENUM('Pilot','Flight_Attendant','Manager') NOT NULL,
  PRIMARY KEY (ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE address (
  ID VARCHAR(20) NOT NULL,
  City VARCHAR(50) NOT NULL,
  Street VARCHAR(50) NOT NULL,
  House_num INT NOT NULL,
  PRIMARY KEY (ID),
  CONSTRAINT address_ibfk_1 FOREIGN KEY (ID) REFERENCES employee (ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE pilot (
  ID VARCHAR(20) NOT NULL,
  Long_Dist_Training TINYINT(1) NOT NULL,
  PRIMARY KEY (ID),
  CONSTRAINT pilot_ibfk_1 FOREIGN KEY (ID) REFERENCES employee (ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE flight_attendent (
  ID VARCHAR(20) NOT NULL,
  Long_Dist_Training TINYINT(1) NOT NULL,
  PRIMARY KEY (ID),
  CONSTRAINT flight_attendent_ibfk_1 FOREIGN KEY (ID) REFERENCES employee (ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE manager (
  ID VARCHAR(20) NOT NULL,
  Login_pass VARCHAR(100) NOT NULL,
  PRIMARY KEY (ID),
  CONSTRAINT manager_ibfk_1 FOREIGN KEY (ID) REFERENCES employee (ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE air_craft (
  Air_Craft_ID VARCHAR(20) NOT NULL,
  Purchase_Date DATE NOT NULL,
  Manufacturer ENUM('Dassault','Boeing','Airbus') NOT NULL,
  Size ENUM('Large','Small') NOT NULL,
  PRIMARY KEY (Air_Craft_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE aircraft_class (
  Air_Craft_ID VARCHAR(20) NOT NULL,
  Class ENUM('Economy','Business') NOT NULL,
  Row_Num INT NOT NULL,
  Col_Num INT NOT NULL,
  PRIMARY KEY (Air_Craft_ID, Class),
  CONSTRAINT aircraft_class_ibfk_1 FOREIGN KEY (Air_Craft_ID) REFERENCES air_craft (Air_Craft_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE flight (
  Air_Craft_ID VARCHAR(20) NOT NULL,
  Dep_Date DATE NOT NULL,
  Dep_Hour TIME NOT NULL,
  Route_ID INT NOT NULL,
  Arrival_Date DATE DEFAULT NULL,
  Arrival_Time TIME DEFAULT NULL,
  Economy_Price DECIMAL(10,2) NOT NULL,
  Business_Price DECIMAL(10,2) DEFAULT NULL,
  Status ENUM('SCHEDULED','FULLY BOOKED','COMPLETED','CANCELED') NOT NULL,
  PRIMARY KEY (Air_Craft_ID, Dep_Date, Dep_Hour),
  KEY Route_ID (Route_ID),
  CONSTRAINT flight_ibfk_1 FOREIGN KEY (Air_Craft_ID) REFERENCES air_craft (Air_Craft_ID),
  CONSTRAINT flight_ibfk_2 FOREIGN KEY (Route_ID) REFERENCES route (Route_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE flight_crew (
  ID VARCHAR(20) NOT NULL,
  Air_Craft_ID VARCHAR(20) NOT NULL,
  Dep_Date DATE NOT NULL,
  Dep_Hour TIME NOT NULL,
  Role ENUM('Pilot','Flight_Attendant') NOT NULL,
  PRIMARY KEY (ID, Air_Craft_ID, Dep_Date, Dep_Hour),
  KEY Air_Craft_ID (Air_Craft_ID, Dep_Date, Dep_Hour),
  CONSTRAINT flight_crew_ibfk_1 FOREIGN KEY (ID) REFERENCES employee (ID),
  CONSTRAINT flight_crew_ibfk_2 FOREIGN KEY (Air_Craft_ID, Dep_Date, Dep_Hour)
    REFERENCES flight (Air_Craft_ID, Dep_Date, Dep_Hour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE registered_customer (
  Email VARCHAR(100) NOT NULL,
  Passport_Num VARCHAR(20) NOT NULL,
  Birth_Date DATE NOT NULL,
  Joining_Date DATE NOT NULL,
  Password VARCHAR(100) NOT NULL,
  PRIMARY KEY (Email),
  CONSTRAINT registered_customer_ibfk_1 FOREIGN KEY (Email) REFERENCES customer (Email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE phone_numbers (
  Cust_Email VARCHAR(100) NOT NULL,
  Phone_num VARCHAR(20) NOT NULL,
  PRIMARY KEY (Cust_Email, Phone_num),
  CONSTRAINT phone_numbers_ibfk_1 FOREIGN KEY (Cust_Email) REFERENCES customer (Email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE flight_order (
  Order_ID INT NOT NULL AUTO_INCREMENT,
  Email VARCHAR(100) NOT NULL,
  Order_Date DATE NOT NULL,
  Order_status ENUM('Active','Completed','Customer_Canceled','System_Canceled') NOT NULL,
  Total_Paid DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (Order_ID),
  KEY Email (Email),
  CONSTRAINT flight_order_ibfk_1 FOREIGN KEY (Email) REFERENCES customer (Email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE tickets (
  Order_ID INT NOT NULL,
  Air_Craft_ID VARCHAR(20) NOT NULL,
  Dep_Date DATE NOT NULL,
  Dep_Hour TIME NOT NULL,
  Chosen_Row_Num INT NOT NULL,
  Chosen_Col_Num INT NOT NULL,
  Price_Paid DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (Air_Craft_ID, Dep_Date, Dep_Hour, Chosen_Row_Num, Chosen_Col_Num),
  KEY Order_ID (Order_ID),
  CONSTRAINT tickets_ibfk_1 FOREIGN KEY (Order_ID) REFERENCES flight_order (Order_ID),
  CONSTRAINT tickets_ibfk_2 FOREIGN KEY (Air_Craft_ID, Dep_Date, Dep_Hour)
    REFERENCES flight (Air_Craft_ID, Dep_Date, Dep_Hour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------------------
-- Seed data (preserved + extended)
-- --------------------------------------------------------------------

SET FOREIGN_KEY_CHECKS = 0;

-- ROUTES (preserve your IDs 29..38)
INSERT INTO route (Route_ID, Origin, Destination, Duration) VALUES
(29, 'תל אביב', 'אתונה', 2.00),
(30, 'תל אביב', 'ניו יורק', 11.00),
(31, 'תל אביב', 'טוקיו', 13.50),
(32, 'אתונה', 'תל אביב', 2.00),
(33, 'אתונה', 'ניו יורק', 10.50),
(34, 'אתונה', 'טוקיו', 13.00),
(35, 'ניו יורק', 'תל אביב', 11.00),
(36, 'ניו יורק', 'אתונה', 10.50),
(37, 'ניו יורק', 'טוקיו', 14.00),
(38, 'טוקיו', 'תל אביב', 13.50);

ALTER TABLE route AUTO_INCREMENT = 39;

INSERT INTO employee (ID, Full_Name_Heb, Phone_num, Start_Work_Date, Role) VALUES
('P01', 'ישראל ישראלי', '050-101', '2020-01-01', 'Pilot'),
('P02', 'אברהם לוי', '050-102', '2020-01-02', 'Pilot'),
('P03', 'יצחק כהן', '050-103', '2020-01-03', 'Pilot'),
('P04', 'יעקב כץ', '050-104', '2020-01-04', 'Pilot'),
('P05', 'משה רבנו', '050-105', '2020-01-05', 'Pilot'),
('P06', 'אהרן הכהן', '050-106', '2020-01-06', 'Pilot'),
('P07', 'יוסף הצדיק', '050-107', '2020-01-07', 'Pilot'),
('P08', 'דוד המלך', '050-108', '2020-01-08', 'Pilot'),
('P09', 'שלמה החכם', '050-109', '2020-01-09', 'Pilot'),
('P10', 'יהושע בן נון', '050-110', '2020-01-10', 'Pilot'),
('A01', 'מיכל כהן', '052-201', '2021-01-01', 'Flight_Attendant'),
('A02', 'שרה לוי', '052-202', '2021-01-02', 'Flight_Attendant'),
('A03', 'רבקה רז', '052-203', '2021-01-03', 'Flight_Attendant'),
('A04', 'לאה גולד', '052-204', '2021-01-04', 'Flight_Attendant'),
('A05', 'רעיה אברהם', '052-205', '2021-01-05', 'Flight_Attendant'),
('A06', 'נועה זיו', '052-206', '2021-01-06', 'Flight_Attendant'),
('A07', 'עמית חן', '052-207', '2021-01-07', 'Flight_Attendant'),
('A08', 'דנה פרי', '052-208', '2021-01-08', 'Flight_Attendant'),
('A09', 'רוני בר', '052-209', '2021-01-09', 'Flight_Attendant'),
('A10', 'גילת שחם', '052-210', '2021-01-10', 'Flight_Attendant'),
('A11', 'מאיה דור', '052-211', '2021-01-11', 'Flight_Attendant'),
('A12', 'לירון גל', '052-212', '2021-01-12', 'Flight_Attendant'),
('A13', 'שירה אור', '052-213', '2021-01-13', 'Flight_Attendant'),
('A14', 'נטע ים', '052-214', '2021-01-14', 'Flight_Attendant'),
('A15', 'הגר נח', '052-215', '2021-01-15', 'Flight_Attendant'),
('A16', 'תמר צבי', '052-216', '2021-01-16', 'Flight_Attendant'),
('A17', 'אילה נון', '052-217', '2021-01-17', 'Flight_Attendant'),
('A18', 'מורן שי', '052-218', '2021-01-18', 'Flight_Attendant'),
('A19', 'אורלי פז', '052-219', '2021-01-19', 'Flight_Attendant'),
('A20', 'שני לב', '052-220', '2021-01-20', 'Flight_Attendant'),
('111', 'יובל לנדאו', '054-0000000', '2026-01-10', 'Manager'),
('112', 'נועה כהן', '054-0000003', '2026-01-11', 'Manager'),
('P11', 'אלון שרון', '050-111', '2020-01-11', 'Pilot'),
('P12', 'עידו מזרחי', '050-112', '2020-01-12', 'Pilot'),
('P13', 'נועם ברק', '050-113', '2020-01-13', 'Pilot'),
('P14', 'ליאור קדם', '050-114', '2020-01-14', 'Pilot'),
('P15', 'איתי רון', '050-115', '2020-01-15', 'Pilot'),
('A21', 'טליה לוי', '052-221', '2021-01-21', 'Flight_Attendant'),
('A22', 'שקד אורי', '052-222', '2021-01-22', 'Flight_Attendant'),
('A23', 'מאי דגן', '052-223', '2021-01-23', 'Flight_Attendant'),
('A24', 'עדי נבון', '052-224', '2021-01-24', 'Flight_Attendant'),
('A25', 'יעל ממן', '052-225', '2021-01-25', 'Flight_Attendant'),
('A26', 'רז כהן', '052-226', '2021-01-26', 'Flight_Attendant'),
('A27', 'ניב סלע', '052-227', '2021-01-27', 'Flight_Attendant');

INSERT INTO address (ID, City, Street, House_num) VALUES
('P01','ת"א','הרצל',1),('P02','ת"א','בן יהודה',2),('P03','ת"א','דיזינגוף',3),('P04','חיפה','הנביאים',4),('P05','חיפה','יפו',5),
('P06','ירושלים','קינג גורג',6),('P07','ירושלים','עזה',7),('P08','נתניה','הרצל',8),('P09','אשדוד','העצמאות',9),('P10','באר שבע','ביאליק',10),
('A01','חולון','סוקולוב',11),('A02','חולון','אילת',12),('A03','בת ים','יוספטל',13),('A04','בת ים','העצמאות',14),('A05','ראשון','רוטשילד',15),
('A06','ראשון','הרצל',16),('A07','פתח תקווה','ההסתדרות',17),('A08','פתח תקווה','המגשימים',18),('A09','רמת גן','ביאליק',19),('A10','רמת גן','הרא"ה',20),
('A11','גבעתיים','כצנלסון',21),('A12','גבעתיים','ויצמן',22),('A13','רעננה','אחוזה',23),('A14','רעננה','הנגב',24),('A15','כפר סבא','ויצמן',25),
('A16','כפר סבא','ירושלים',26),('A17','הוד השרון','הבנים',27),('A18','הוד השרון','החקלאים',28),('A19','מודיעין','העמק',29),('A20','מודיעין','השפלה',30),
('111','ת"א','הירקון',100),
('112','רמת גן','הבונים',12),
('P11','ת"א','אלנבי',31),
('P12','חיפה','הרצל',12),
('P13','ירושלים','יפו',45),
('P14','נתניה','סוקולוב',7),
('P15','באר שבע','העצמאות',9),
('A21','רמת השרון','הגליל',3),
('A22','רעננה','השרון',8),
('A23','כפר סבא','ויצמן',40),
('A24','גבעתיים','בורוכוב',15),
('A25','מודיעין','הנחל',6),
('A26','פתח תקווה','זבוטינסקי',22),
('A27','חולון','הנגב',19);

INSERT INTO pilot (ID, Long_Dist_Training) VALUES
('P01',1),('P02',1),('P03',1),('P04',1),('P05',1),
('P06',0),('P07',0),('P08',0),('P09',0),('P10',0),
('P11',0),('P12',0),('P13',0),('P14',0),('P15',0);

INSERT INTO flight_attendent (ID, Long_Dist_Training) VALUES
('A01',1),('A02',1),('A03',1),('A04',1),('A05',1),('A06',1),('A07',1),('A08',1),('A09',1),('A10',1),
('A11',0),('A12',0),('A13',0),('A14',0),('A15',0),('A16',0),('A17',0),('A18',0),('A19',0),('A20',0),
('A21',0),('A22',0),('A23',0),('A24',0),('A25',0),('A26',0),('A27',0);

INSERT INTO manager (ID, Login_pass) VALUES
('111', '123456'),
('112', '123456');


INSERT INTO air_craft (Air_Craft_ID, Purchase_Date, Manufacturer, Size) VALUES
('AC01', '2015-05-20', 'Boeing', 'Large'),
('AC02', '2018-10-12', 'Airbus', 'Small'),
('AC03', '2020-01-01', 'Boeing', 'Large'),
('AC04', '2019-03-15', 'Dassault', 'Small'),
('AC05', '2021-06-30', 'Airbus', 'Large'),
('AC06', '2017-08-22', 'Boeing', 'Small');

INSERT INTO aircraft_class (Air_Craft_ID, Class, Row_Num, Col_Num) VALUES
('AC01','Economy',30,6),('AC01','Business',5,4),
('AC03','Economy',30,6),('AC03','Business',5,4),
('AC05','Economy',30,6),('AC05','Business',5,4),
('AC02','Economy',15,4),
('AC04','Economy',15,4),
('AC06','Economy',15,4);


INSERT INTO customer (Email, Full_Name_Eng) VALUES
('yoni@gmail.com', 'Yonatan Hugi'),
('stav@gmail.com', 'Stav Ben Avraham'),
('guest1@gmail.com', 'Dana Guest'),
('guest2@gmail.com', 'Omer Guest');

INSERT INTO registered_customer (Email, Passport_Num, Birth_Date, Joining_Date, Password) VALUES
('yoni@gmail.com', 'P1234567', '1995-01-01', '2026-01-10', '123456'),
('stav@gmail.com', 'P7654321', '1996-01-01', '2026-01-10', '123456');

INSERT INTO phone_numbers (Cust_Email, Phone_num) VALUES
('yoni@gmail.com', '054-0000001'),
('stav@gmail.com', '054-0000002'),
('guest1@gmail.com', '054-0000007'),
('guest2@gmail.com', '054-0000008');


INSERT INTO flight
(Air_Craft_ID, Dep_Date, Dep_Hour, Route_ID, Arrival_Date, Arrival_Time, Economy_Price, Business_Price, Status) VALUES
('AC01', '2026-02-01', '10:00:00', 29, NULL, NULL, 300.00, 900.00, 'SCHEDULED'),
('AC02', '2026-02-03', '09:30:00', 30, NULL, NULL, 520.00, NULL,  'SCHEDULED'),
('AC03', '2026-02-05', '14:00:00', 33, NULL, NULL, 410.00, 980.00, 'SCHEDULED'),
('AC04', '2026-02-07', '08:15:00', 35, NULL, NULL, 540.00, NULL,  'SCHEDULED'),
('AC05', '2026-02-09', '12:00:00', 31, NULL, NULL, 650.00, 1400.00, 'CANCELED'),
('AC06', '2026-01-10', '16:45:00', 32, '2026-01-10', '18:45:00', 280.00, NULL, 'COMPLETED');



INSERT INTO flight_crew (ID, Air_Craft_ID, Dep_Date, Dep_Hour, Role) VALUES
('P01','AC01','2026-02-01','10:00:00','Pilot'),
('P02','AC01','2026-02-01','10:00:00','Pilot'),
('P03','AC01','2026-02-01','10:00:00','Pilot'),
('A01','AC01','2026-02-01','10:00:00','Flight_Attendant'),
('A02','AC01','2026-02-01','10:00:00','Flight_Attendant'),
('A03','AC01','2026-02-01','10:00:00','Flight_Attendant'),
('A04','AC01','2026-02-01','10:00:00','Flight_Attendant'),
('A05','AC01','2026-02-01','10:00:00','Flight_Attendant'),
('A06','AC01','2026-02-01','10:00:00','Flight_Attendant'),

-- AC03 (Large)  Athens -> NY
('P04','AC03','2026-02-05','14:00:00','Pilot'),
('P05','AC03','2026-02-05','14:00:00','Pilot'),
('P06','AC03','2026-02-05','14:00:00','Pilot'),
('A07','AC03','2026-02-05','14:00:00','Flight_Attendant'),
('A08','AC03','2026-02-05','14:00:00','Flight_Attendant'),
('A09','AC03','2026-02-05','14:00:00','Flight_Attendant'),
('A10','AC03','2026-02-05','14:00:00','Flight_Attendant'),
('A11','AC03','2026-02-05','14:00:00','Flight_Attendant'),
('A12','AC03','2026-02-05','14:00:00','Flight_Attendant'),

-- AC05 (Large)  TLV -> Tokyo (Canceled)
('P07','AC05','2026-02-09','12:00:00','Pilot'),
('P08','AC05','2026-02-09','12:00:00','Pilot'),
('P09','AC05','2026-02-09','12:00:00','Pilot'),
('A13','AC05','2026-02-09','12:00:00','Flight_Attendant'),
('A14','AC05','2026-02-09','12:00:00','Flight_Attendant'),
('A15','AC05','2026-02-09','12:00:00','Flight_Attendant'),
('A16','AC05','2026-02-09','12:00:00','Flight_Attendant'),
('A17','AC05','2026-02-09','12:00:00','Flight_Attendant'),
('A18','AC05','2026-02-09','12:00:00','Flight_Attendant'),

-- AC02 (Small)  TLV -> NY
('P10','AC02','2026-02-03','09:30:00','Pilot'),
('P11','AC02','2026-02-03','09:30:00','Pilot'),
('A19','AC02','2026-02-03','09:30:00','Flight_Attendant'),
('A20','AC02','2026-02-03','09:30:00','Flight_Attendant'),
('A21','AC02','2026-02-03','09:30:00','Flight_Attendant'),

-- AC04 (Small)  NY -> TLV
('P12','AC04','2026-02-07','08:15:00','Pilot'),
('P13','AC04','2026-02-07','08:15:00','Pilot'),
('A22','AC04','2026-02-07','08:15:00','Flight_Attendant'),
('A23','AC04','2026-02-07','08:15:00','Flight_Attendant'),
('A24','AC04','2026-02-07','08:15:00','Flight_Attendant'),

-- AC06 (Small)  Athens -> TLV (Completed)
('P14','AC06','2026-01-10','16:45:00','Pilot'),
('P15','AC06','2026-01-10','16:45:00','Pilot'),
('A25','AC06','2026-01-10','16:45:00','Flight_Attendant'),
('A26','AC06','2026-01-10','16:45:00','Flight_Attendant'),
('A27','AC06','2026-01-10','16:45:00','Flight_Attendant');


INSERT INTO flight_order (Email, Order_Date, Order_status, Total_Paid)
VALUES ('yoni@gmail.com', '2026-01-20', 'Active', 600.00);
SET @o1 := LAST_INSERT_ID();
INSERT INTO tickets (Order_ID, Air_Craft_ID, Dep_Date, Dep_Hour, Chosen_Row_Num, Chosen_Col_Num, Price_Paid) VALUES
(@o1,'AC01','2026-02-01','10:00:00', 6, 1, 300.00),
(@o1,'AC01','2026-02-01','10:00:00', 6, 2, 300.00);


INSERT INTO flight_order (Email, Order_Date, Order_status, Total_Paid)
VALUES ('stav@gmail.com', '2026-01-21', 'Active', 520.00);
SET @o2 := LAST_INSERT_ID();
INSERT INTO tickets VALUES
(@o2,'AC02','2026-02-03','09:30:00', 3, 1, 520.00);


INSERT INTO flight_order (Email, Order_Date, Order_status, Total_Paid)
VALUES ('yoni@gmail.com', '2026-01-10', 'Completed', 280.00);
SET @o3 := LAST_INSERT_ID();
INSERT INTO tickets VALUES
(@o3,'AC06','2026-01-10','16:45:00', 10, 2, 280.00);


INSERT INTO flight_order (Email, Order_Date, Order_status, Total_Paid)
VALUES ('stav@gmail.com', '2026-01-22', 'Customer_Canceled', 820.00);
SET @o4 := LAST_INSERT_ID();
INSERT INTO tickets VALUES
(@o4,'AC03','2026-02-05','14:00:00', 7, 1, 410.00),
(@o4,'AC03','2026-02-05','14:00:00', 7, 2, 410.00);


INSERT INTO flight_order (Email, Order_Date, Order_status, Total_Paid)
VALUES ('guest1@gmail.com', '2026-01-23', 'Active', 1620.00);
SET @o5 := LAST_INSERT_ID();
INSERT INTO tickets VALUES
(@o5,'AC04','2026-02-07','08:15:00', 5, 1, 540.00),
(@o5,'AC04','2026-02-07','08:15:00', 5, 2, 540.00),
(@o5,'AC04','2026-02-07','08:15:00', 5, 3, 540.00);


INSERT INTO flight_order (Email, Order_Date, Order_status, Total_Paid)
VALUES ('guest2@gmail.com', '2026-01-24', 'Completed', 900.00);
SET @o6 := LAST_INSERT_ID();
INSERT INTO tickets VALUES
(@o6,'AC01','2026-02-01','10:00:00', 1, 1, 900.00);

SET FOREIGN_KEY_CHECKS = 1;