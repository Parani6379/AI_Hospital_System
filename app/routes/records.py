from flask import Blueprint, request, jsonify, render_template
from ..database import get_db
from ..auth_utils import token_required
from ..services import generate_record_hash

records_bp = Blueprint('records', __name__)

@records_bp.route('/records')
def records_page():
    return render_template('records.html')

@records_bp.route('/api/records/<int:patient_id>')
@token_required
def get_records(patient_id):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT r.*, d.name as doctor_name
               FROM medical_records r
               LEFT JOIN doctors d ON r.doctor_id = d.id
               WHERE r.patient_id=? ORDER BY r.created_at DESC""",
            (patient_id,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@records_bp.route('/api/records', methods=['POST'])
@token_required
def add_record():
    d = request.get_json()
    if not d or not d.get('patient_id'):
        return jsonify({'error': 'patient_id is required'}), 400
    rh = generate_record_hash(
        d['patient_id'], d.get('record_type', 'consultation'),
        d.get('notes', ''), d.get('prescription', '')
    )
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO medical_records
               (patient_id, doctor_id, record_type, notes, prescription, record_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (d['patient_id'], d.get('doctor_id'),
             d.get('record_type', 'consultation'),
             d.get('notes', ''), d.get('prescription', ''), rh)
        )
        rid = cur.lastrowid
        conn.commit()
        r = conn.execute("SELECT * FROM medical_records WHERE id=?", (rid,)).fetchone()
        return jsonify(dict(r)), 201
    finally:
        conn.close()

@records_bp.route('/api/records/<int:rid>/verify')
@token_required
def verify(rid):
    conn = get_db()
    try:
        r = conn.execute("SELECT * FROM medical_records WHERE id=?", (rid,)).fetchone()
        if not r:
            return jsonify({'error': 'Not found'}), 404
        new_hash = generate_record_hash(
            r['patient_id'], r['record_type'], r['notes'], r['prescription']
        )
        return jsonify({'record_id': rid, 'is_valid': new_hash == r['record_hash'], 'hash': r['record_hash']})
    finally:
        conn.close()

@records_bp.route('/api/records/all')
@token_required
def all_records():
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT r.*, p.name as patient_name, d.name as doctor_name
               FROM medical_records r
               LEFT JOIN patients p ON r.patient_id = p.id
               LEFT JOIN doctors  d ON r.doctor_id  = d.id
               ORDER BY r.created_at DESC LIMIT 100"""
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()