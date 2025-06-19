from flask import Flask, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

# Inicializar la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"

# Inicializar la base de datos
from src.models import db
db.init_app(app)

# Registrar blueprints
from src.routes.auth import auth_bp
from src.routes.trademark import trademark_bp
from src.routes.subscription import subscription_bp
from src.routes.alert import alert_bp
from src.routes.integration import integration_bp

app.register_blueprint(auth_bp)
app.register_blueprint(trademark_bp)
app.register_blueprint(subscription_bp)
app.register_blueprint(alert_bp)
app.register_blueprint(integration_bp)

# Ruta principal
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('dashboard.html')
    return render_template('index.html')

# Ruta para el panel de control
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

# Manejador de errores 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Manejador de errores 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Crear tablas de la base de datos
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
