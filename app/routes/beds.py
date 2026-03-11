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
    conn = get_db()
    try:
        beds = conn.execute("SELECT * FROM beds ORDER BY ward, bed_number").fetchall()
        result = []
        for b in beds:
            bd = dict(b)
            p = conn.execute(
                "SELECT id,name,age,severity_label,severity_score FROM patients WHERE bed_id=?",
                (b['id'],)
            ).fetchone()
            bd['patient'] = dict(p) if p else None
            result.append(bd)
        return jsonify(result)
    finally:
        conn.close()

@beds_bp.route('/api/beds/stats')
@token_required
def bed_stats():
    conn = get_db()
    try:
        # Use a single query to get counts for all bed types
        stats = conn.execute(
            """SELECT bed_type, 
                      COUNT(*) as total, 
                      SUM(is_occupied) as occupied
               FROM beds 
               GROUP BY bed_type"""
        ).fetchall()
        
        by_type = {}
        total = 0
        occupied_total = 0
        
        for row in stats:
            bt = row['bed_type']
            tot = row['total']
            occ = row['occupied'] or 0
            by_type[bt] = {'total': tot, 'occupied': occ, 'free': tot - occ}
            total += tot
            occupied_total += occ
            
        # Ensure all standard types exist in the result
        for t in ['general', 'icu', 'emergency', 'isolation']:
            if t not in by_type:
                by_type[t] = {'total': 0, 'occupied': 0, 'free': 0}

        return jsonify({
            'total': total, 'occupied': occupied_total, 'free': total - occupied_total,
            'by_type': by_type,
            'occupancy_rate': round(occupied_total / total * 100, 1) if total else 0
        })
    finally:
        conn.close()

@beds_bp.route('/api/beds/allocate/<int:patient_id>', methods=['POST'])
@token_required
def allocate(patient_id):
    conn = get_db()
    try:
        p = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        if not p:
            return jsonify({'error': 'Patient not found'}), 404
        if p['bed_id']:
            return jsonify({'error': 'Patient already has a bed'}), 400

        bed = find_best_bed(p['severity_score'], p['status'], p['infection_risk'], conn=conn)
        if not bed:
            return jsonify({'error': 'No beds available'}), 404

        # Use shared service function
        days = allocate_bed(patient_id, bed['id'], p['severity_score'], p['age'] or 40, conn=conn)
        conn.commit()
        
        return jsonify({
            'message': 'Bed allocated',
            'bed': bed,
            'predicted_discharge_days': days
        })
    finally:
        conn.close()

@beds_bp.route('/api/beds/release/<int:bed_id>', methods=['POST'])
@token_required
def release(bed_id):
    # Use shared service function
    release_bed(bed_id)
    conn = get_db()
    try:
        bed = conn.execute("SELECT * FROM beds WHERE id=?", (bed_id,)).fetchone()
        return jsonify({'message': 'Bed released', 'bed': dict(bed) if bed else {}})
    finally:
        conn.close()