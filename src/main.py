import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets

# Inicializar SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuración de la aplicación
    app.config['SECRET_KEY'] = secrets.token_hex(16)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marca_tracker.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Registrar blueprints
    from src.routes.auth import auth_bp
    from src.routes.dashboard import dashboard_bp
    from src.routes.trademark import trademark_bp
    from src.routes.subscription import subscription_bp
    from src.routes.alert import alert_bp
    from src.routes.integration import integration_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(trademark_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(integration_bp)
    
    # Crear tablas de la base de datos
    with app.app_context():
        db.create_all()
        
        # Crear usuario administrador predeterminado
        from src.models.user import User
        from werkzeug.security import generate_password_hash
        
        # Verificar si el usuario admin ya existe
        admin_user = User.query.filter_by(email='admin@admin.com').first()
        if not admin_user:
            # Crear usuario administrador
            admin = User(
                nombre='Administrador',
                apellido='Sistema',
                email='admin@admin.com',
                password=generate_password_hash('admin', method='pbkdf2:sha256'),
                plan='empresarial',
                fecha_registro=datetime.utcnow(),
                ultimo_acceso=datetime.utcnow(),
                activo=True,
                es_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    
    # Ruta principal
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Manejador de errores 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    # Manejador de errores 500
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)
