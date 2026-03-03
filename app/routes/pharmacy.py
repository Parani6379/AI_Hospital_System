from flask import Blueprint, request, jsonify, render_template
from ..database import get_db
from ..auth_utils import token_required
from ..ai_modules import demand_forecaster
from datetime import datetime

pharmacy_bp = Blueprint('pharmacy', __name__)

@pharmacy_bp.route('/pharmacy')
def pharmacy_page():
    return render_template('pharmacy.html')

@pharmacy_bp.route('/api/pharmacy/stock')
@token_required
def stock():
    conn = get_db()
    meds = conn.execute("SELECT *, (stock < threshold) as is_low FROM medicines ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(m) for m in meds])

@pharmacy_bp.route('/api/pharmacy/forecast/<int:mid>')
@token_required
def forecast(mid):
    conn = get_db()
    m    = conn.execute("SELECT * FROM medicines WHERE id=?", (mid,)).fetchone()
    conn.close()
    if not m: return jsonify({'error': 'Not found'}), 404
    base   = m['threshold'] // 2
    recent = [max(0, base + (i % 5)) for i in range(14)]
    fc     = demand_forecaster.forecast_7days(recent)
    return jsonify({
        'medicine_id': mid, 'medicine_name': m['name'],
        'current_stock': m['stock'], 'forecast_7days': fc,
        'total_needed': sum(fc), 'alert': m['stock'] < sum(fc),
        'days_remaining': m['stock'] // max(sum(fc) // 7, 1)
    })

@pharmacy_bp.route('/api/pharmacy/alerts')
@token_required
def alerts():
    conn = get_db()
    rows = conn.execute("SELECT *, (threshold-stock) as shortage FROM medicines WHERE stock<threshold").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@pharmacy_bp.route('/api/pharmacy/restock', methods=['POST'])
@token_required
def restock():
    d    = request.get_json()
    conn = get_db()
    conn.execute("UPDATE medicines SET stock=stock+? WHERE id=?", (d.get('quantity', 0), d.get('medicine_id')))
    conn.commit()
    m = conn.execute("SELECT * FROM medicines WHERE id=?", (d['medicine_id'],)).fetchone()
    conn.close()
    return jsonify({'message': 'Stock updated', 'medicine': dict(m)})

@pharmacy_bp.route('/api/pharmacy/procurement/auto', methods=['POST'])
@token_required
def auto_procurement():
    conn  = get_db()
    lows  = conn.execute("SELECT * FROM medicines WHERE stock < threshold").fetchall()
    orders = []
    for m in lows:
        base   = m['threshold'] // 2
        recent = [max(0, base + (i % 5)) for i in range(14)]
        fc     = demand_forecaster.forecast_7days(recent)
        needed = sum(fc)
        order_qty = max(needed * 2, m['threshold'] * 3)
        orders.append({
            'medicine_id': m['id'], 'medicine_name': m['name'],
            'current_stock': m['stock'], 'threshold': m['threshold'],
            'forecast_need': needed, 'order_quantity': int(order_qty),
            'priority': 'URGENT' if m['stock'] == 0 else 'HIGH',
            'generated_at': datetime.utcnow().isoformat()
        })
    conn.close()
    return jsonify({'total_orders': len(orders), 'procurement_orders': orders})

@pharmacy_bp.route('/api/pharmacy/procurement/confirm', methods=['POST'])
@token_required
def confirm_procurement():
    d    = request.get_json()
    conn = get_db()
    for order in d.get('orders', []):
        conn.execute("UPDATE medicines SET stock=stock+? WHERE id=?", (order['order_quantity'], order['medicine_id']))
    conn.commit()
    conn.close()
    return jsonify({'message': f"Procurement confirmed for {len(d.get('orders', []))} medicines"})