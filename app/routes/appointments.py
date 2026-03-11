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
    conn = get_db()
    try:
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
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@appointments_bp.route('/api/appointments', methods=['POST'])
@token_required
def add_appointment():
    d = request.get_json()
    if not d or not d.get('patient_id') or not d.get('doctor_id'):
        return jsonify({'error': 'patient_id and doctor_id are required'}), 400
    conn = get_db()
    try:
        slot_date = d.get('slot_time', '')[:10]
        existing = conn.execute(
            """SELECT COUNT(*) FROM appointments
               WHERE doctor_id=? AND slot_time LIKE ? AND status='scheduled'""",
            (d['doctor_id'], f"{slot_date}%")
        ).fetchone()[0]
        wait_time = existing * 15
        cur = conn.execute(
            """INSERT INTO appointments
               (patient_id, doctor_id, slot_time, wait_time, status, notes)
               VALUES (?, ?, ?, ?, 'scheduled', ?)""",
            (d['patient_id'], d['doctor_id'],
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
        return jsonify(dict(row)), 201
    finally:
        conn.close()

@appointments_bp.route('/api/appointments/<int:aid>', methods=['PUT'])
@token_required
def update_appointment(aid):
    d = request.get_json()
    if not d:
        return jsonify({'error': 'Request body required'}), 400
    allowed_fields = ['status', 'notes', 'slot_time']
    conn = get_db()
    try:
        for field in allowed_fields:
            if field in d:
                conn.execute(f"UPDATE appointments SET {field}=? WHERE id=?", (d[field], aid))
        conn.commit()
        row = conn.execute("SELECT * FROM appointments WHERE id=?", (aid,)).fetchone()
        if not row:
            return jsonify({'error': 'Appointment not found'}), 404
        return jsonify(dict(row))
    finally:
        conn.close()

@appointments_bp.route('/api/appointments/<int:aid>', methods=['DELETE'])
@token_required
def delete_appointment(aid):
    conn = get_db()
    try:
        conn.execute("DELETE FROM appointments WHERE id=?", (aid,))
        conn.commit()
        return jsonify({'message': 'Deleted'})
    finally:
        conn.close()