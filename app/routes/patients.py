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
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM patients WHERE status=? ORDER BY severity_score DESC",
                (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM patients ORDER BY severity_score DESC"
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@patients_bp.route('/api/patients/<int:pid>')
@token_required
def get_patient(pid):
    conn = get_db()
    try:
        p = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
        if not p:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(dict(p))
    finally:
        conn.close()

@patients_bp.route('/api/patients', methods=['POST'])
@token_required
def add_patient():
    d = request.get_json()
    if not d or not d.get('name'):
        return jsonify({'error': 'Patient name is required'}), 400
    hr    = d.get('heart_rate', 75)
    bp    = d.get('bp_systolic', 120)
    o2    = d.get('oxygen_level', 98)
    temp  = d.get('temperature', 37.0)
    age   = d.get('age', 40)
    score = severity_model.predict(hr, bp, o2, temp, age)
    label = severity_model.classify(score)
    days  = discharge_pred.predict_days(score, age)
    conn  = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO patients
               (name,age,gender,blood_group,contact,emergency_contact,
                diagnosis,severity_score,severity_label,infection_risk,
                status,predicted_discharge_days,doctor_id)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d['name'], age, d.get('gender'), d.get('blood_group'),
             d.get('contact'), d.get('emergency_contact'), d.get('diagnosis'),
             score, label, d.get('infection_risk', 'low'),
             d.get('status', 'admitted'), days, d.get('doctor_id'))
        )
        pid = cur.lastrowid
        conn.commit()
        p = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
        return jsonify(dict(p)), 201
    finally:
        conn.close()

@patients_bp.route('/api/patients/<int:pid>', methods=['PUT'])
@token_required
def update_patient(pid):
    d = request.get_json()
    if not d:
        return jsonify({'error': 'Request body required'}), 400
    allowed_fields = ['name','age','gender','diagnosis','infection_risk','status','doctor_id']
    conn = get_db()
    try:
        # Build update query dynamically for requested fields
        updates = []
        params = []
        for field in allowed_fields:
            if field in d:
                updates.append(f"{field}=?")
                params.append(d[field])
        
        if updates:
            params.append(pid)
            conn.execute(f"UPDATE patients SET {', '.join(updates)} WHERE id=?", params)

        if d.get('status') == 'discharged':
            p = conn.execute("SELECT bed_id FROM patients WHERE id=?", (pid,)).fetchone()
            if p and p['bed_id']:
                from ..services import release_bed
                # Pass existing connection to participate in same transaction
                release_bed(p['bed_id'], conn=conn)
            else:
                # If no bed, still ensure discharge fields are set
                conn.execute(
                    "UPDATE patients SET status='discharged', discharge_date=datetime('now') WHERE id=?",
                    (pid,)
                )
        
        conn.commit()
        p = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
        if not p:
            return jsonify({'error': 'Patient not found'}), 404
        return jsonify(dict(p))
    finally:
        conn.close()

@patients_bp.route('/api/patients/<int:pid>', methods=['DELETE'])
@token_required
def delete_patient(pid):
    conn = get_db()
    try:
        p = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone()
        if not p:
            return jsonify({'error': 'Patient not found'}), 404
        if p['bed_id']:
            conn.execute("UPDATE beds SET is_occupied=0 WHERE id=?", (p['bed_id'],))
        # Delete dependent records first (FK constraints)
        conn.execute("DELETE FROM vitals WHERE patient_id=?", (pid,))
        conn.execute("DELETE FROM medical_records WHERE patient_id=?", (pid,))
        conn.execute("DELETE FROM appointments WHERE patient_id=?", (pid,))
        conn.execute("DELETE FROM patients WHERE id=?", (pid,))
        conn.commit()
        return jsonify({'message': 'Deleted'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500
    finally:
        conn.close()