import hashlib, json
from datetime import datetime
from .database import get_db
from .ai_modules import discharge_pred, demand_forecaster, burnout_detector

def generate_record_hash(patient_id, record_type, notes, prescription):
    data = json.dumps({
        'pid': patient_id, 'type': record_type,
        'notes': notes, 'presc': prescription
    }, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()

def check_vitals_alerts(data):
    alerts = []
    
    hr = data.get('heart_rate')
    if hr is not None:
        if hr < 40 or hr > 140:
            alerts.append({'type': 'heart_rate', 'value': hr, 'level': 'critical', 'msg': 'CRITICAL EXTREME', 'min': 50, 'max': 120})
        elif hr < 50 or hr > 120:
            alerts.append({'type': 'heart_rate', 'value': hr, 'level': 'warning', 'msg': 'Abnormal Warning', 'min': 50, 'max': 120})

    o2 = data.get('oxygen_level')
    if o2 is not None:
        if o2 < 90:
            alerts.append({'type': 'oxygen_level', 'value': o2, 'level': 'critical', 'msg': 'CRITICAL LOW', 'min': 95, 'max': 100})
        elif o2 < 95:
            alerts.append({'type': 'oxygen_level', 'value': o2, 'level': 'warning', 'msg': 'Low Warning', 'min': 95, 'max': 100})
            
    bp = data.get('bp_systolic')
    if bp is not None:
        if bp < 70 or bp > 200:
            alerts.append({'type': 'bp_systolic', 'value': bp, 'level': 'critical', 'msg': 'CRITICAL EXTREME', 'min': 90, 'max': 180})
        elif bp < 90 or bp > 180:
            alerts.append({'type': 'bp_systolic', 'value': bp, 'level': 'warning', 'msg': 'Abnormal Warning', 'min': 90, 'max': 180})
            
    temp = data.get('temperature')
    if temp is not None:
        if temp > 40.0:
            alerts.append({'type': 'temperature', 'value': temp, 'level': 'critical', 'msg': 'CRITICAL HIGH', 'min': 35.0, 'max': 39.0})
        elif temp < 35.0 or temp > 39.0:
            alerts.append({'type': 'temperature', 'value': temp, 'level': 'warning', 'msg': 'Abnormal Warning', 'min': 35.0, 'max': 39.0})

    return alerts

def find_best_bed(severity_score, status, infection_risk, conn=None):
    if severity_score >= 75:       bed_type = 'icu'
    elif infection_risk == 'high': bed_type = 'isolation'
    elif status == 'emergency':    bed_type = 'emergency'
    else:                          bed_type = 'general'
    own_conn = conn is None
    if own_conn:
        conn = get_db()
    try:
        bed = conn.execute(
            "SELECT * FROM beds WHERE is_occupied=0 AND bed_type=? LIMIT 1",
            (bed_type,)
        ).fetchone()
        if not bed:
            bed = conn.execute(
                "SELECT * FROM beds WHERE is_occupied=0 LIMIT 1"
            ).fetchone()
        return dict(bed) if bed else None
    finally:
        if own_conn:
            conn.close()

def allocate_bed(patient_id, bed_id, severity, age, conn=None):
    days = discharge_pred.predict_days(severity, age)
    own_conn = conn is None
    if own_conn:
        conn = get_db()
    try:
        conn.execute("UPDATE beds SET is_occupied=1 WHERE id=?", (bed_id,))
        conn.execute(
            "UPDATE patients SET bed_id=?, predicted_discharge_days=? WHERE id=?",
            (bed_id, days, patient_id)
        )
        if own_conn:
            conn.commit()
        return days
    finally:
        if own_conn:
            conn.close()

def release_bed(bed_id, conn=None):
    own_conn = conn is None
    if own_conn:
        conn = get_db()
    try:
        conn.execute("UPDATE beds SET is_occupied=0 WHERE id=?", (bed_id,))
        conn.execute(
            "UPDATE patients SET bed_id=NULL, status='discharged', "
            "discharge_date=datetime('now') WHERE bed_id=?",
            (bed_id,)
        )
        if own_conn:
            conn.commit()
    finally:
        if own_conn:
            conn.close()

def get_doctor_analytics(doctor_id, doctor_name, department):
    conn = get_db()
    try:
        appt_count = conn.execute(
            "SELECT COUNT(*) FROM appointments WHERE doctor_id=?", (doctor_id,)
        ).fetchone()[0]
        patient_count = conn.execute(
            "SELECT COUNT(*) FROM patients WHERE doctor_id=? AND status='admitted'",
            (doctor_id,)
        ).fetchone()[0]
    finally:
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