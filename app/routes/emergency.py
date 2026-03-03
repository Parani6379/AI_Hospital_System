from flask import Blueprint, request, jsonify, render_template
from ..database import get_db
from ..auth_utils import token_required
from ..ai_modules import severity_model

emergency_bp = Blueprint('emergency', __name__)

@emergency_bp.route('/emergency')
def emergency_page():
    return render_template('emergency.html')

@emergency_bp.route('/api/emergency/assess', methods=['POST'])
@token_required
def assess():
    d     = request.get_json()
    score = severity_model.predict(
        d.get('heart_rate', 75), d.get('bp_systolic', 120),
        d.get('oxygen_level', 98), d.get('temperature', 37.0),
        d.get('age', 40)
    )
    label  = severity_model.classify(score)
    routes = {
        'critical': {'ward': 'ICU',       'bed_type': 'icu',       'priority': 1, 'action': 'Immediate ICU Admission + Doctor Alert'},
        'moderate': {'ward': 'Emergency', 'bed_type': 'emergency', 'priority': 2, 'action': 'Emergency Ward + 15 min Consultation'},
        'stable':   {'ward': 'OPD',       'bed_type': 'general',   'priority': 3, 'action': 'Regular OPD Queue + Scheduled Slot'}
    }
    return jsonify({'score': score, 'label': label, 'route': routes[label]})

@emergency_bp.route('/api/emergency/queue')
@token_required
def queue():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM patients WHERE status IN ('emergency','admitted') "
        "ORDER BY severity_score DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])