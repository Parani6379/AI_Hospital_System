import jwt, os
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

SECRET = os.getenv('JWT_SECRET_KEY', 'aihas_jwt_dev_secret_2024')

def create_token(user_id, role, name):
    payload = {
        'id': user_id, 'role': role, 'name': name,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')

def decode_token(token):
    return jwt.decode(token, SECRET, algorithms=['HS256'])

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth  = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
        if not token:
            return jsonify({'error': 'Token missing'}), 401

        try:
            request.user = decode_token(token)
        except jwt.ExpiredSignatureError:
            # Auto clear expired token from DB
            try:
                payload = jwt.decode(
                    token, options={"verify_signature": False}
                )
                user_id = payload.get('id')
                if user_id:
                    from .database import get_db
                    conn = get_db()
                    conn.execute(
                        "UPDATE users SET active_token=NULL WHERE id=?",
                        (user_id,)
                    )
                    conn.commit()
                    conn.close()
            except Exception:
                pass
            return jsonify({'error': 'Token expired. Please login again.'}), 401
        except Exception:
            return jsonify({'error': 'Invalid token'}), 401

        # Validate token matches DB active session
        try:
            from .database import get_db
            conn = get_db()
            user = conn.execute(
                "SELECT active_token FROM users WHERE id=?",
                (request.user['id'],)
            ).fetchone()
            conn.close()
            if not user or user['active_token'] != token:
                return jsonify({'error': 'Session expired. Please login again.'}), 401
        except Exception:
            pass

        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = None
            auth  = request.headers.get('Authorization', '')
            if auth.startswith('Bearer '):
                token = auth[7:]
            if not token:
                return jsonify({'error': 'Token missing'}), 401
            try:
                request.user = decode_token(token)
            except Exception:
                return jsonify({'error': 'Invalid token'}), 401
            if request.user.get('role') not in roles:
                return jsonify({'error': 'Access denied'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def hash_password(pwd):
    return generate_password_hash(pwd)

def verify_password(pwd, hashed):
    return check_password_hash(hashed, pwd)