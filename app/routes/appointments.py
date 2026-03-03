from flask import Blueprint, request, jsonify, render_template
from ..database import get_db
from ..auth_utils import token_required

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/appointments')
def appointments_page():
    return render_template('appointments.html')

@appointments_bp.route('/api/appointments')
@token_required
def get_appointments():
    status = request.args.get('status')
    conn   = get_db()
    if status:
        rows = conn.execute(
            """SELECT a.*, p.name as patient_name, d.name as doctor_name, d.department
               FROM appointments a
               LEFT JOIN patients p ON a.patient_id = p.id
               LEFT JOIN doctors  d ON a.doctor_id  = d.id
               WHERE a.status=? ORDER BY a.slot_time ASC""", (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT a.*, p.name as patient_name, d.name as doctor_name, d.department
               FROM appointments a
               LEFT JOIN patients p ON a.patient_id = p.id
               LEFT JOIN doctors  d ON a.doctor_id  = d.id
               ORDER BY a.slot_time ASC"""
        ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@appointments_bp.route('/api/appointments', methods=['POST'])
@token_required
def add_appointment():
    d    = request.get_json()
    conn = get_db()
    slot_date = d.get('slot_time', '')[:10]
    existing  = conn.execute(
        """SELECT COUNT(*) FROM appointments
           WHERE doctor_id=? AND slot_time LIKE ? AND status='scheduled'""",
        (d.get('doctor_id'), f"{slot_date}%")
    ).fetchone()[0]
    wait_time = existing * 15
    cur = conn.execute(
        """INSERT INTO appointments
           (patient_id, doctor_id, slot_time, wait_time, status, notes)
           VALUES (?, ?, ?, ?, 'scheduled', ?)""",
        (d.get('patient_id'), d.get('doctor_id'),
         d.get('slot_time'), wait_time, d.get('notes', ''))
    )
    aid = cur.lastrowid
    conn.commit()
    row = conn.execute(
        """SELECT a.*, p.name as patient_name, d.name as doctor_name
           FROM appointments a
           LEFT JOIN patients p ON a.patient_id = p.id
           LEFT JOIN doctors  d ON a.doctor_id  = d.id
           WHERE a.id=?""", (aid,)
    ).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@appointments_bp.route('/api/appointments/<int:aid>', methods=['PUT'])
@token_required
def update_appointment(aid):
    d    = request.get_json()
    conn = get_db()
    for field in ['status', 'notes', 'slot_time']:
        if field in d:
            conn.execute(f"UPDATE appointments SET {field}=? WHERE id=?", (d[field], aid))
    conn.commit()
    row = conn.execute("SELECT * FROM appointments WHERE id=?", (aid,)).fetchone()
    conn.close()
    return jsonify(dict(row))

@appointments_bp.route('/api/appointments/<int:aid>', methods=['DELETE'])
@token_required
def delete_appointment(aid):
    conn = get_db()
    conn.execute("DELETE FROM appointments WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})