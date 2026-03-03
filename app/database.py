import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'aihas.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
 CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'nurse',
        contact TEXT,
        is_active INTEGER DEFAULT 1,
        active_token TEXT DEFAULT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        department TEXT,
        contact TEXT
    );
    CREATE TABLE IF NOT EXISTS beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bed_number TEXT UNIQUE NOT NULL,
        ward TEXT,
        bed_type TEXT DEFAULT 'general',
        is_occupied INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        blood_group TEXT,
        contact TEXT,
        emergency_contact TEXT,
        diagnosis TEXT,
        severity_score REAL DEFAULT 0,
        severity_label TEXT DEFAULT 'stable',
        infection_risk TEXT DEFAULT 'low',
        status TEXT DEFAULT 'admitted',
        admission_date TEXT DEFAULT (datetime('now')),
        discharge_date TEXT,
        predicted_discharge_days INTEGER,
        bed_id INTEGER REFERENCES beds(id),
        doctor_id INTEGER REFERENCES doctors(id)
    );
    CREATE TABLE IF NOT EXISTS vitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL REFERENCES patients(id),
        heart_rate REAL,
        bp_systolic REAL,
        bp_diastolic REAL,
        oxygen_level REAL,
        temperature REAL,
        alert_triggered INTEGER DEFAULT 0,
        alert_message TEXT,
        recorded_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        stock INTEGER DEFAULT 0,
        threshold INTEGER DEFAULT 50,
        unit TEXT DEFAULT 'tablets',
        unit_price REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS medical_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL REFERENCES patients(id),
        doctor_id INTEGER,
        record_type TEXT,
        notes TEXT,
        prescription TEXT,
        record_hash TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER REFERENCES patients(id),
        doctor_id INTEGER REFERENCES doctors(id),
        slot_time TEXT,
        wait_time INTEGER DEFAULT 0,
        status TEXT DEFAULT 'scheduled',
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()