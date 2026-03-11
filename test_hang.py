print("[1] flask Blueprint", flush=True)
from flask import Blueprint
print("[2] db get_db", flush=True)
from app.database import get_db
print("[3] auth_utils create_token", flush=True)
from app.auth_utils import create_token
print("[4] pyjwt", flush=True)
import jwt as pyjwt
print("[done]", flush=True)
