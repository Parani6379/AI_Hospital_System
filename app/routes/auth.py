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
    d = request.get_json()
    if not d:
        return jsonify({'error': 'Request body required'}), 400
    if not d.get('name') or not d.get('email') or not d.get('password'):
        return jsonify({'error': 'Name, email and password are required'}), 400
    conn = get_db()
    try:
        if conn.execute("SELECT id FROM users WHERE email=?", (d['email'],)).fetchone():
            return jsonify({'error': 'Email already exists'}), 409
        conn.execute(
            "INSERT INTO users(name,email,password,role,contact) VALUES(?,?,?,?,?)",
            (d['name'], d['email'], hash_password(d['password']),
             d.get('role', 'nurse'), d.get('contact', ''))
        )
        conn.commit()
        return jsonify({'message': 'User created'}), 201
    finally:
        conn.close()

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    d = request.get_json()
    if not d or not d.get('email') or not d.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE email=?", (d['email'],)
        ).fetchone()

        if not user or not verify_password(d['password'], user['password']):
            return jsonify({'error': 'Invalid email or password'}), 401

        # Single session enforcement
        if user['active_token']:
            try:
                pyjwt.decode(user['active_token'], SECRET, algorithms=['HS256'])
                # Valid token exists — check if it's the same browser re-logging-in
                # (e.g. page refresh or tab reopen). Allow re-login by clearing old token.
                conn.execute(
                    "UPDATE users SET active_token=NULL WHERE id=?", (user['id'],)
                )
                conn.commit()
            except pyjwt.ExpiredSignatureError:
                # Token expired — clear stale token and allow fresh login
                conn.execute(
                    "UPDATE users SET active_token=NULL WHERE id=?", (user['id'],)
                )
                conn.commit()
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

        return jsonify({
            'token': token,
            'role':  user['role'],
            'name':  user['name'],
            'id':    user['id']
        }), 200
    finally:
        conn.close()

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    token = None
    auth  = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]

    if token:
        try:
            # Decode without verifying expiry (but verify signature)
            payload = pyjwt.decode(
                token, SECRET,
                algorithms=['HS256'],
                options={"verify_exp": False}
            )
            user_id = payload.get('id')
            if user_id:
                conn = get_db()
                try:
                    conn.execute(
                        "UPDATE users SET active_token=NULL WHERE id=?", (user_id,)
                    )
                    conn.commit()
                finally:
                    conn.close()
        except Exception:
            pass

    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/api/auth/clear-session', methods=['POST'])
def clear_session():
    """Used by Force Logout button on login page"""
    d = request.get_json()
    if not d:
        return jsonify({'error': 'Request body required'}), 400
    email = d.get('email', '')
    if not email:
        return jsonify({'error': 'Email required'}), 400
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id FROM users WHERE email=?", (email,)
        ).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        conn.execute(
            "UPDATE users SET active_token=NULL WHERE email=?", (email,)
        )
        conn.commit()
        return jsonify({'message': f'Session cleared for {email}'}), 200
    finally:
        conn.close()

@auth_bp.route('/api/auth/me')
@token_required
def me():
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id,name,email,role FROM users WHERE id=?",
            (request.user['id'],)
        ).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(dict(user)), 200
    finally:
        conn.close()