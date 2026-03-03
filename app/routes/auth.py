from flask import Blueprint, request, jsonify, render_template, redirect
from ..database import get_db
from ..auth_utils import create_token, hash_password, verify_password, token_required, SECRET
import jwt as pyjwt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect('/login')

@auth_bp.route('/login')
def login_page():
    return render_template('login.html')

@auth_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    d    = request.get_json()
    conn = get_db()
    if conn.execute("SELECT id FROM users WHERE email=?", (d['email'],)).fetchone():
        conn.close()
        return jsonify({'error': 'Email already exists'}), 409
    conn.execute(
        "INSERT INTO users(name,email,password,role,contact) VALUES(?,?,?,?,?)",
        (d['name'], d['email'], hash_password(d['password']),
         d.get('role', 'nurse'), d.get('contact', ''))
    )
    conn.commit()
    conn.close()
    return jsonify({'message': 'User created'}), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    d    = request.get_json()
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email=?", (d.get('email', ''),)
    ).fetchone()

    if not user or not verify_password(d.get('password', ''), user['password']):
        conn.close()
        return jsonify({'error': 'Invalid email or password'}), 401

    # Single session enforcement
    if user['active_token']:
        try:
            pyjwt.decode(user['active_token'], SECRET, algorithms=['HS256'])
            # Valid token exists — user genuinely logged in elsewhere
            conn.close()
            return jsonify({
                'error': 'Already logged in on another device. Please logout first or ask admin to clear your session.'
            }), 403
        except pyjwt.ExpiredSignatureError:
            # Token expired but user never logged out — still block
            conn.close()
            return jsonify({
                'error': 'Already logged in on another device. Please logout first or ask admin to clear your session.'
            }), 403
        except Exception:
            # Corrupt or invalid token — clear and allow login
            conn.execute(
                "UPDATE users SET active_token=NULL WHERE id=?", (user['id'],)
            )
            conn.commit()

    # Create new token and save to DB
    token = create_token(user['id'], user['role'], user['name'])
    conn.execute(
        "UPDATE users SET active_token=? WHERE id=?", (token, user['id'])
    )
    conn.commit()
    conn.close()

    return jsonify({
        'token': token,
        'role':  user['role'],
        'name':  user['name'],
        'id':    user['id']
    }), 200

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    token = None
    auth  = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]

    if token:
        try:
            # Decode without verifying signature or expiry
            payload = pyjwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            user_id = payload.get('id')
            if user_id:
                conn = get_db()
                conn.execute(
                    "UPDATE users SET active_token=NULL WHERE id=?", (user_id,)
                )
                conn.commit()
                conn.close()
        except Exception:
            pass

    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/api/auth/clear-session', methods=['POST'])
def clear_session():
    """Used by Force Logout button on login page"""
    d     = request.get_json()
    email = d.get('email', '')
    if not email:
        return jsonify({'error': 'Email required'}), 400
    conn = get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email=?", (email,)
    ).fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    conn.execute(
        "UPDATE users SET active_token=NULL WHERE email=?", (email,)
    )
    conn.commit()
    conn.close()
    return jsonify({'message': f'Session cleared for {email}'}), 200

@auth_bp.route('/api/auth/me')
@token_required
def me():
    conn = get_db()
    user = conn.execute(
        "SELECT id,name,email,role FROM users WHERE id=?",
        (request.user['id'],)
    ).fetchone()
    conn.close()
    return jsonify(dict(user)), 200