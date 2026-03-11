print("loading auth", flush=True)
from .auth         import auth_bp
print("loading patients", flush=True)
from .patients     import patients_bp
print("loading beds", flush=True)
from .beds         import beds_bp
print("loading emergency", flush=True)
from .emergency    import emergency_bp
print("loading vitals", flush=True)
from .vitals       import vitals_bp
print("loading pharmacy", flush=True)
from .pharmacy     import pharmacy_bp
print("loading analytics", flush=True)
from .analytics    import analytics_bp
print("loading records", flush=True)
from .records      import records_bp
print("loading appointments", flush=True)
from .appointments import appointments_bp

def register_routes(app):
    for bp in [auth_bp, patients_bp, beds_bp, emergency_bp,
               vitals_bp, pharmacy_bp, analytics_bp, records_bp,
               appointments_bp]:
        app.register_blueprint(bp)