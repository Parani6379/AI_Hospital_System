from flask import Blueprint, request, jsonify, render_template
from ..database import get_db
from ..auth_utils import token_required
from ..ai_modules import severity_model, discharge_pred

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/patients')
def patients_page():
    return render_template('patients.html')

@patients_bp.route('/api/patients')
@token_required
def get_patients():
    status = request.args.get('status')
    conn   = get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM patients WHERE status=? ORDER BY severity_score DESC",
            (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM patients ORDER BY severity_score DESC"
        ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@patients_bp.route('/api/patients/<int:pid>')
@token_required
def get_patient(pid):
    conn = get_db()
    p    = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not p:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(p))

@patients_bp.route('/api/patients', methods=['POST'])
@token_required
def add_patient():
    d     = request.get_json()
    hr    = d.get('heart_rate', 75)
    bp    = d.get('bp_systolic', 120)
    o2    = d.get('oxygen_level', 98)
    temp  = d.get('temperature', 37.0)
    age   = d.get('age', 40)
    score = severity_model.predict(hr, bp, o2, temp, age)
    label = severity_model.classify(score)
    days  = discharge_pred.predict_days(score, age)
    conn  = get_db()
    cur   = conn.execute(
        """INSERT INTO patients
           (name,age,gender,blood_group,contact,emergency_contact,
            diagnosis,severity_score,severity_label,infection_risk,
            status,predicted_discharge_days,doctor_id)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (d.get('name'), age, d.get('gender'), d.get('blood_group'),
         d.get('contact'), d.get('emergency_contact'), d.get('diagnosis'),
         score, label, d.get('infection_risk', 'low'),
         d.get('status', 'admitted'), days, d.get('doctor_id'))
    )
    pid = cur.lastrowid
    conn.commit()
    p   = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    conn.close()
    return jsonify(dict(p)), 201

@patients_bp.route('/api/patients/<int:pid>', methods=['PUT'])
@token_required
def update_patient(pid):
    d    = request.get_json()
    conn = get_db()
    for field in ['name','age','gender','diagnosis','infection_risk','status','doctor_id']:
        if field in d:
            conn.execute(
                f"UPDATE patients SET {field}=? WHERE id=?", (d[field], pid)
            )
    if d.get('status') == 'discharged':
        p = conn.execute("SELECT bed_id FROM patients WHERE id=?", (pid,)).fetchone()
        if p and p['bed_id']:
            conn.execute("UPDATE beds SET is_occupied=0 WHERE id=?", (p['bed_id'],))
        conn.execute(
            "UPDATE patients SET bed_id=NULL, discharge_date=datetime('now') WHERE id=?",
            (pid,)
        )
    conn.commit()
    p    = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    conn.close()
    return jsonify(dict(p))

@patients_bp.route('/api/patients/<int:pid>', methods=['DELETE'])
@token_required
def delete_patient(pid):
    conn = get_db()
    p    = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
    if p and p['bed_id']:
        conn.execute("UPDATE beds SET is_occupied=0 WHERE id=?", (p['bed_id'],))
    conn.execute("DELETE FROM patients WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})