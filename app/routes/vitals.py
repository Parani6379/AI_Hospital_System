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
    d      = request.get_json()
    alerts = check_vitals_alerts(d)
    msg    = '; '.join([f"{a['type']}={a['value']}" for a in alerts]) if alerts else None
    if alerts:
        print(f"\n🚨 ALERT Patient#{patient_id}: {msg}")
    conn = get_db()
    cur  = conn.execute(
        """INSERT INTO vitals
           (patient_id,heart_rate,bp_systolic,bp_diastolic,
            oxygen_level,temperature,alert_triggered,alert_message)
           VALUES(?,?,?,?,?,?,?,?)""",
        (patient_id, d.get('heart_rate'), d.get('bp_systolic'),
         d.get('bp_diastolic'), d.get('oxygen_level'), d.get('temperature'),
         1 if alerts else 0, msg)
    )
    vid = cur.lastrowid
    conn.commit()
    v   = conn.execute("SELECT * FROM vitals WHERE id=?", (vid,)).fetchone()
    conn.close()
    return jsonify({'status': 'recorded', 'vitals': dict(v), 'alerts': alerts}), 201

@vitals_bp.route('/api/vitals/<int:patient_id>')
@token_required
def latest(patient_id):
    conn = get_db()
    v    = conn.execute(
        "SELECT * FROM vitals WHERE patient_id=? ORDER BY recorded_at DESC LIMIT 1",
        (patient_id,)
    ).fetchone()
    conn.close()
    return jsonify(dict(v) if v else {})

@vitals_bp.route('/api/vitals/<int:patient_id>/history')
@token_required
def history(patient_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM vitals WHERE patient_id=? ORDER BY recorded_at DESC LIMIT 50",
        (patient_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@vitals_bp.route('/api/vitals/alerts/recent')
@token_required
def recent_alerts():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM vitals WHERE alert_triggered=1 ORDER BY recorded_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])