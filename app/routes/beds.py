from flask import Blueprint, request, jsonify, render_template
from ..database import get_db
from ..auth_utils import token_required
from ..services import find_best_bed, allocate_bed, release_bed

beds_bp = Blueprint('beds', __name__)

@beds_bp.route('/beds')
def beds_page():
    return render_template('beds.html')

@beds_bp.route('/api/beds')
@token_required
def get_beds():
    conn   = get_db()
    beds   = conn.execute("SELECT * FROM beds ORDER BY ward, bed_number").fetchall()
    result = []
    for b in beds:
        bd = dict(b)
        p  = conn.execute(
            "SELECT id,name,age,severity_label,severity_score FROM patients WHERE bed_id=?",
            (b['id'],)
        ).fetchone()
        bd['patient'] = dict(p) if p else None
        result.append(bd)
    conn.close()
    return jsonify(result)

@beds_bp.route('/api/beds/stats')
@token_required
def bed_stats():
    conn     = get_db()
    total    = conn.execute("SELECT COUNT(*) FROM beds").fetchone()[0]
    occupied = conn.execute("SELECT COUNT(*) FROM beds WHERE is_occupied=1").fetchone()[0]
    by_type  = {}
    for t in ['general', 'icu', 'emergency', 'isolation']:
        tot = conn.execute(
            "SELECT COUNT(*) FROM beds WHERE bed_type=?", (t,)
        ).fetchone()[0]
        occ = conn.execute(
            "SELECT COUNT(*) FROM beds WHERE bed_type=? AND is_occupied=1", (t,)
        ).fetchone()[0]
        by_type[t] = {'total': tot, 'occupied': occ, 'free': tot - occ}
    conn.close()
    return jsonify({
        'total': total, 'occupied': occupied, 'free': total - occupied,
        'by_type': by_type,
        'occupancy_rate': round(occupied / total * 100, 1) if total else 0
    })

@beds_bp.route('/api/beds/allocate/<int:patient_id>', methods=['POST'])
@token_required
def allocate(patient_id):
    conn = get_db()
    p    = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    conn.close()
    if not p:           return jsonify({'error': 'Patient not found'}), 404
    if p['bed_id']:     return jsonify({'error': 'Patient already has a bed'}), 400
    bed = find_best_bed(p['severity_score'], p['status'], p['infection_risk'])
    if not bed:         return jsonify({'error': 'No beds available'}), 404
    days = allocate_bed(patient_id, bed['id'], p['severity_score'], p['age'] or 40)
    return jsonify({
        'message': 'Bed allocated',
        'bed': bed,
        'predicted_discharge_days': days
    })

@beds_bp.route('/api/beds/release/<int:bed_id>', methods=['POST'])
@token_required
def release(bed_id):
    release_bed(bed_id)
    conn = get_db()
    bed  = conn.execute("SELECT * FROM beds WHERE id=?", (bed_id,)).fetchone()
    conn.close()
    return jsonify({'message': 'Bed released', 'bed': dict(bed) if bed else {}})