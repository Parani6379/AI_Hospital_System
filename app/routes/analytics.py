from flask import Blueprint, request, jsonify, render_template
from ..database import get_db
from ..auth_utils import token_required
from ..services import get_doctor_analytics

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def analytics_page():
    return render_template('analytics.html')

@analytics_bp.route('/api/analytics/doctors')
@token_required
def all_doctors():
    conn = get_db()
    try:
        doctors = conn.execute("SELECT * FROM doctors").fetchall()
        return jsonify([get_doctor_analytics(d['id'], d['name'], d['department']) for d in doctors])
    finally:
        conn.close()

@analytics_bp.route('/api/analytics/dashboard')
@token_required
def dashboard_stats():
    conn = get_db()
    try:
        total     = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        admitted  = conn.execute("SELECT COUNT(*) FROM patients WHERE status='admitted'").fetchone()[0]
        emergency = conn.execute("SELECT COUNT(*) FROM patients WHERE status='emergency'").fetchone()[0]
        discharged= conn.execute("SELECT COUNT(*) FROM patients WHERE status='discharged'").fetchone()[0]
        t_beds    = conn.execute("SELECT COUNT(*) FROM beds").fetchone()[0]
        occ       = conn.execute("SELECT COUNT(*) FROM beds WHERE is_occupied=1").fetchone()[0]
        alrt      = conn.execute("SELECT COUNT(*) FROM vitals WHERE alert_triggered=1 AND DATE(recorded_at)=DATE('now')").fetchone()[0]
        docs      = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
        return jsonify({
            'patients': {'total': total, 'admitted': admitted,
                         'emergency': emergency, 'discharged': discharged},
            'beds':     {'total': t_beds, 'occupied': occ, 'free': t_beds - occ,
                         'occupancy_rate': round(occ / t_beds * 100, 1) if t_beds else 0},
            'alerts':   {'total': alrt},
            'doctors':  {'total': docs}
        })
    finally:
        conn.close()

@analytics_bp.route('/api/doctors')
@token_required
def get_doctors():
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM doctors").fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()