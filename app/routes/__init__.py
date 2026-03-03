from .auth         import auth_bp
from .patients     import patients_bp
from .beds         import beds_bp
from .emergency    import emergency_bp
from .vitals       import vitals_bp
from .pharmacy     import pharmacy_bp
from .analytics    import analytics_bp
from .records      import records_bp
from .appointments import appointments_bp

def register_routes(app):
    for bp in [auth_bp, patients_bp, beds_bp, emergency_bp,
               vitals_bp, pharmacy_bp, analytics_bp, records_bp,
               appointments_bp]:
        app.register_blueprint(bp)