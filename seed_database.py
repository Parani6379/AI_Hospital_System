import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import get_db, init_db
from app.auth_utils import hash_password

def seed():
    init_db()
    conn = get_db()

    # Users
    users = [
        ('Admin User',   'admin@hospital.com',  'admin123',  'admin'),
        ('Dr. Smith',    'doctor@hospital.com', 'doctor123', 'doctor'),
        ('Nurse Jane',   'nurse@hospital.com',  'nurse123',  'nurse'),
    ]
    for name, email, pwd, role in users:
        if not conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            conn.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                         (name, email, hash_password(pwd), role))

    # Doctors
    doctors = [
        ('Dr. Sarah Johnson', 'Cardiology',    'Cardiology'),
        ('Dr. Mike Chen',     'Neurology',     'Neurology'),
        ('Dr. Emily Davis',   'Orthopedics',   'Orthopedics'),
        ('Dr. James Wilson',  'Emergency Med', 'Emergency'),
        ('Dr. Lisa Brown',    'ICU',           'Critical Care'),
    ]
    for name, spec, dept in doctors:
        if not conn.execute("SELECT id FROM doctors WHERE name=?", (name,)).fetchone():
            conn.execute("INSERT INTO doctors(name,specialization,department) VALUES(?,?,?)",
                         (name, spec, dept))

    # Beds
    beds = []
    for i in range(1, 21):  beds.append((f'G{i:02d}', 'General Ward', 'general'))
    for i in range(1, 11):  beds.append((f'ICU{i:02d}', 'ICU', 'icu'))
    for i in range(1, 6):   beds.append((f'E{i:02d}', 'Emergency', 'emergency'))
    for i in range(1, 6):   beds.append((f'ISO{i:02d}', 'Isolation', 'isolation'))
    for bn, ward, bt in beds:
        if not conn.execute("SELECT id FROM beds WHERE bed_number=?", (bn,)).fetchone():
            conn.execute("INSERT INTO beds(bed_number,ward,bed_type) VALUES(?,?,?)", (bn, ward, bt))

    # Medicines
    medicines = [
        ('Paracetamol',  'Analgesic',    200, 50),
        ('Amoxicillin',  'Antibiotic',   150, 60),
        ('Metformin',    'Antidiabetic',  80, 40),
        ('Atorvastatin', 'Statin',        30, 50),
        ('Aspirin',      'Antiplatelet', 120, 45),
        ('Ibuprofen',    'NSAID',         45, 50),
        ('Lisinopril',   'ACE Inhibitor', 25, 40),
        ('Omeprazole',   'PPI',          160, 55),
        ('Insulin',      'Hormone',       18, 30),
        ('Morphine',     'Opioid',        12, 20),
    ]
    for name, cat, stock, thresh in medicines:
        if not conn.execute("SELECT id FROM medicines WHERE name=?", (name,)).fetchone():
            conn.execute("INSERT INTO medicines(name,category,stock,threshold) VALUES(?,?,?,?)",
                         (name, cat, stock, thresh))

    # Sample patients
    from app.ai_modules import severity_model, discharge_pred
    sample_patients = [
        ('Alice Johnson', 45, 'Female', 'A+',  'Hypertension',      90,  160, 95,   37.2, 'admitted',  'low'),
        ('Bob Martinez',  67, 'Male',   'O+',  'Diabetes Mellitus', 85,  140, 97,   38.1, 'admitted',  'medium'),
        ('Carol White',   32, 'Female', 'B+',  'Appendicitis',      110, 130, 96,   38.8, 'emergency', 'low'),
        ('David Brown',   78, 'Male',   'AB-', 'Heart Failure',     130, 180, 88,   39.2, 'emergency', 'high'),
        ('Emma Davis',    55, 'Female', 'O-',  'Pneumonia',         95,  145, 92,   39.5, 'admitted',  'high'),
    ]
    for name, age, gender, blood, diag, hr, bp, o2, temp, status, inf in sample_patients:
        if not conn.execute("SELECT id FROM patients WHERE name=?", (name,)).fetchone():
            score = severity_model.predict(hr, bp, o2, temp, age)
            label = severity_model.classify(score)
            days  = discharge_pred.predict_days(score, age)
            cur = conn.execute(
                """INSERT INTO patients
                   (name, age, gender, blood_group, diagnosis,
                    severity_score, severity_label, infection_risk,
                    status, predicted_discharge_days)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, age, gender, blood, diag,
                 score, label, inf, status, days)
            )
            pid = cur.lastrowid
            # Store initial vitals in the vitals table
            conn.execute(
                """INSERT INTO vitals
                   (patient_id, heart_rate, bp_systolic, oxygen_level, temperature)
                   VALUES (?, ?, ?, ?, ?)""",
                (pid, hr, bp, o2, temp)
            )

    conn.commit()
    conn.close()
    print("✅ Database seeded successfully!")
    print("   Login: admin@hospital.com / admin123")

if __name__ == '__main__':
    seed()