import hashlib, json
from datetime import datetime
from .database import get_db
from .ai_modules import discharge_pred, demand_forecaster, burnout_detector

THRESHOLDS = {
    'heart_rate':   (40, 130),
    'oxygen_level': (90, 100),
    'bp_systolic':  (70, 180),
    'temperature':  (35.0, 39.5)
}

def generate_record_hash(patient_id, record_type, notes, prescription):
    ts = datetime.utcnow().isoformat()
    data = json.dumps({
        'pid': patient_id, 'type': record_type,
        'notes': notes, 'presc': prescription, 'ts': ts
    }, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()

def check_vitals_alerts(data):
    alerts = []
    for key, (lo, hi) in THRESHOLDS.items():
        v = data.get(key)
        if v is not None and (v < lo or v > hi):
            alerts.append({'type': key, 'value': v, 'min': lo, 'max': hi})
    return alerts

def find_best_bed(severity_score, status, infection_risk):
    if severity_score >= 75:       bed_type = 'icu'
    elif infection_risk == 'high': bed_type = 'isolation'
    elif status == 'emergency':    bed_type = 'emergency'
    else:                          bed_type = 'general'
    conn = get_db()
    bed = conn.execute(
        "SELECT * FROM beds WHERE is_occupied=0 AND bed_type=? LIMIT 1",
        (bed_type,)
    ).fetchone()
    if not bed:
        bed = conn.execute(
            "SELECT * FROM beds WHERE is_occupied=0 LIMIT 1"
        ).fetchone()
    conn.close()
    return dict(bed) if bed else None

def allocate_bed(patient_id, bed_id, severity, age):
    days = discharge_pred.predict_days(severity, age)
    conn = get_db()
    conn.execute("UPDATE beds SET is_occupied=1 WHERE id=?", (bed_id,))
    conn.execute(
        "UPDATE patients SET bed_id=?, predicted_discharge_days=? WHERE id=?",
        (bed_id, days, patient_id)
    )
    conn.commit()
    conn.close()
    return days

def release_bed(bed_id):
    conn = get_db()
    conn.execute("UPDATE beds SET is_occupied=0 WHERE id=?", (bed_id,))
    conn.execute(
        "UPDATE patients SET bed_id=NULL, status='discharged', "
        "discharge_date=datetime('now') WHERE bed_id=?",
        (bed_id,)
    )
    conn.commit()
    conn.close()

def get_doctor_analytics(doctor_id, doctor_name, department):
    conn = get_db()
    appt_count = conn.execute(
        "SELECT COUNT(*) FROM appointments WHERE doctor_id=?", (doctor_id,)
    ).fetchone()[0]
    patient_count = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE doctor_id=? AND status='admitted'",
        (doctor_id,)
    ).fetchone()[0]
    conn.close()
    avg_patients  = appt_count / 30
    avg_hours     = min(avg_patients * 0.5 + 4, 14)
    overtime_days = max(0, int((avg_hours - 8) * 30 / 24))
    risk = burnout_detector.predict_risk(avg_hours, avg_patients, overtime_days)
    return {
        'doctor_id': doctor_id, 'doctor_name': doctor_name,
        'department': department or 'General',
        'total_appointments': appt_count,
        'active_patients': patient_count,
        'avg_patients_per_day': round(avg_patients, 2),
        'avg_hours_per_day':    round(avg_hours, 2),
        'overtime_days': overtime_days,
        'burnout_risk':  risk
    }