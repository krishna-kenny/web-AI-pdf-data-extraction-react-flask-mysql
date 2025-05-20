# MySQL DDL Statements
# --------------------
# Run these statements in your MySQL client to create the required tables.

# 1. Invoice Table
# ----------------
# VendorCode: VARCHAR, PO_No: VARCHAR, InvNo: VARCHAR (PRIMARY KEY), InvRefNo: VARCHAR, InvDate: DATE,
# InvPeriod: VARCHAR, HSN_SAC: VARCHAR (nullable), ShipmentMode: VARCHAR, GST_RCM: BOOLEAN,
# InvStatus: VARCHAR

invoice_ddl = """
CREATE TABLE IF NOT EXISTS invoice (
    VendorCode VARCHAR(50) NOT NULL,
    PONumber VARCHAR(50),
    InvNo VARCHAR(50) NOT NULL,
    InvRefNo VARCHAR(50),
    InvDate DATE,
    InvPeriod VARCHAR(50),
    HSN_SAC VARCHAR(50),
    ShipmentMode VARCHAR(50),
    GST_RCM BOOLEAN DEFAULT FALSE,
    InvStatus VARCHAR(20),
    PRIMARY KEY (InvNo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# 2. Shipments Table
# ------------------
# SrNo: INT AUTO_INCREMENT PRIMARY KEY,
# ShipmentDate: DATE, ShipmentNo: INT (nullable), Packets: INT,
# InvoiceNo: VARCHAR foreign key to invoice.InvNo,
# SAPPONo: VARCHAR, Docket: VARCHAR, VehicleNo: VARCHAR,
# VehicleType: VARCHAR, Origin: VARCHAR, Destination: VARCHAR

shipments_ddl = """
CREATE TABLE IF NOT EXISTS shipments (
    SrNo INT AUTO_INCREMENT,
    ShipmentDate DATE,
    ShipmentNo INT,
    Packets INT,
    InvoiceNo VARCHAR(50),
    SAPPONo VARCHAR(50),
    Docket VARCHAR(50),
    VehicleNo VARCHAR(50),
    VehicleType VARCHAR(100),
    Origin VARCHAR(100),
    Destination VARCHAR(100),
    PRIMARY KEY (SrNo),
    FOREIGN KEY (InvoiceNo) REFERENCES invoice(InvNo)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Python Script: load_and_insert.py
# ---------------------------------
# This script connects to MySQL, reads two CSV files (invoice.csv, shipments.csv),
# and inserts the records into the respective tables.

import mysql.connector
import csv
import datetime

# --- Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'your_database',
    'raise_on_warnings': True
}

# --- Helper Functions ---

def parse_date(date_str):
    """
    Parse date strings like "Apr 16, 2025" into datetime.date objects.
    """
    try:
        return datetime.datetime.strptime(date_str.strip(), '%b %d, %Y').date()
    except Exception:
        return None

# --- Main Workflow ---

def load_invoice_data(csv_file):
    """Read invoice CSV and return list of dicts"""
    records = []
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                'VendorCode': row.get('Vendor Code'),
                'PONumber': row.get('PO No.'),
                'InvNo': row.get('Inv No'),
                'InvRefNo': row.get('Inv Ref No.'),
                'InvDate': parse_date(row.get('Inv Date', '')),
                'InvPeriod': row.get('Inv Period'),
                'HSN_SAC': row.get('HSN / SAC:'),
                'ShipmentMode': row.get('Shipment Mode'),
                'GST_RCM': True if row.get('GST Payable under RCM:','').strip().upper().startswith('Y') else False,
                'InvStatus': row.get('Inv Status')
            })
    return records


def load_shipments_data(csv_file):
    """Read shipments CSV and return list of dicts"""
    records = []
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # skip empty lines
            if not row.get('Inv No'):
                continue
            records.append({
                'ShipmentDate': parse_date(row.get('Shipment Date', '')),
                'ShipmentNo': int(row.get('Shipment No', 0)) if row.get('Shipment No') else None,
                'Packets': int(row.get('Packets', 0)),
                'InvoiceNo': row.get('Invoice No'),
                'SAPPONo': row.get('SAP PO No'),
                'Docket': row.get('Docket'),
                'VehicleNo': row.get('Vehicle No'),
                'VehicleType': row.get('Vehicle Type'),
                'Origin': row.get('From'),
                'Destination': row.get('To')
            })
    return records


def insert_records():
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()

    # Create tables if not exists
    cursor.execute(invoice_ddl)
    cursor.execute(shipments_ddl)

    # Load data
    invoices = load_invoice_data('invoice.csv')
    shipments = load_shipments_data('shipments.csv')

    # Insert invoices
    inv_insert = ("INSERT IGNORE INTO invoice"
                  " (VendorCode,PONumber,InvNo,InvRefNo,InvDate,InvPeriod,HSN_SAC,ShipmentMode,GST_RCM,InvStatus)"
                  " VALUES (%(VendorCode)s,%(PONumber)s,%(InvNo)s,%(InvRefNo)s,%(InvDate)s,%(InvPeriod)s,%(HSN_SAC)s,%(ShipmentMode)s,%(GST_RCM)s,%(InvStatus)s)")
    for inv in invoices:
        cursor.execute(inv_insert, inv)

    # Insert shipments
    ship_insert = ("INSERT INTO shipments"
                   " (ShipmentDate,ShipmentNo,Packets,InvoiceNo,SAPPONo,Docket,VehicleNo,VehicleType,Origin,Destination)"
                   " VALUES (%(ShipmentDate)s,%(ShipmentNo)s,%(Packets)s,%(InvoiceNo)s,%(SAPPONo)s,%(Docket)s,%(VehicleNo)s,%(VehicleType)s,%(Origin)s,%(Destination)s)")
    for ship in shipments:
        cursor.execute(ship_insert, ship)

    cnx.commit()
    cursor.close()
    cnx.close()

if __name__ == '__main__':
    insert_records()
    print("Data imported successfully.")
