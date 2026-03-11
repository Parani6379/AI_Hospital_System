from flask import Blueprint, request, jsonify, render_template
from ..database import get_db
from ..auth_utils import token_required
from ..services import check_vitals_alerts

vitals_bp = Blueprint('vitals', __name__)

@vitals_bp.route('/vitals')
def vitals_page():
    return render_template('vitals.html')

@vitals_bp.route('/api/vitals/push/<int:patient_id>', methods=['POST'])
@token_required
def push(patient_id):
    d = request.get_json()
    if not d:
        return jsonify({'error': 'Request body required'}), 400
    alerts = check_vitals_alerts(d)
    msg = '; '.join([f"{a['type']} {a['level'].upper()}: {a['value']}" for a in alerts]) if alerts else None
    conn = get_db()
    try:
        # Always insert a new vitals record (preserves full history)
        cur = conn.execute(
            """INSERT INTO vitals
               (patient_id,heart_rate,bp_systolic,bp_diastolic,
                oxygen_level,temperature,alert_triggered,alert_message)
               VALUES(?,?,?,?,?,?,?,?)""",
            (patient_id, d.get('heart_rate'), d.get('bp_systolic'),
             d.get('bp_diastolic'), d.get('oxygen_level'), d.get('temperature'),
             1 if alerts else 0, msg)
        )
        vid = cur.lastrowid
        # NOTE: We intentionally do NOT update alert_triggered on old rows.
        # alert_triggered is a permanent historical fact (used by analytics for
        # "Alerts Today" counts). The recent_alerts query handles active-alert
        # deduplication by only returning the latest record per patient.
        conn.commit()
        v = conn.execute("SELECT * FROM vitals WHERE id=?", (vid,)).fetchone()
        return jsonify({'status': 'recorded', 'vitals': dict(v), 'alerts': alerts}), 201
    finally:
        conn.close()

@vitals_bp.route('/api/vitals/<int:patient_id>')
@token_required
def latest(patient_id):
    conn = get_db()
    try:
        v = conn.execute(
            "SELECT * FROM vitals WHERE patient_id=? ORDER BY recorded_at DESC LIMIT 1",
            (patient_id,)
        ).fetchone()
        return jsonify(dict(v) if v else {})
    finally:
        conn.close()

@vitals_bp.route('/api/vitals/<int:patient_id>/history')
@token_required
def history(patient_id):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM vitals WHERE patient_id=? ORDER BY recorded_at DESC LIMIT 50",
            (patient_id,)
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()

@vitals_bp.route('/api/vitals/alerts/recent')
@token_required
def recent_alerts():
    conn = get_db()
    try:
        # Return only the LATEST vital reading per patient that still has an active alert.
        # This prevents stale/resolved alerts from appearing after normal vitals are submitted.
        rows = conn.execute(
            """
            SELECT v.*
            FROM vitals v
            INNER JOIN (
                SELECT patient_id, MAX(recorded_at) AS latest
                FROM vitals
                GROUP BY patient_id
            ) latest_v
              ON v.patient_id = latest_v.patient_id
             AND v.recorded_at = latest_v.latest
            WHERE v.alert_triggered = 1
            ORDER BY v.recorded_at DESC
            LIMIT 20
            """
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()