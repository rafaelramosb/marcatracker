from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__)

# Decorador para verificar si el usuario está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Aquí se obtendría información del usuario y sus marcas desde la base de datos
    # Para esta demo, usamos datos de ejemplo
    return render_template('dashboard.html')

@dashboard_bp.route('/marcas')
@login_required
def marcas():
    # En una implementación completa, aquí se obtendrían las marcas del usuario desde la base de datos
    return render_template('dashboard.html')  # Temporalmente redirigimos al dashboard

@dashboard_bp.route('/alertas')
@login_required
def alertas():
    # En una implementación completa, aquí se obtendrían las alertas del usuario desde la base de datos
    return render_template('dashboard.html')  # Temporalmente redirigimos al dashboard

@dashboard_bp.route('/buscar')
@login_required
def buscar():
    # En una implementación completa, aquí se implementaría la búsqueda de marcas
    return render_template('dashboard.html')  # Temporalmente redirigimos al dashboard

@dashboard_bp.route('/reportes')
@login_required
def reportes():
    # En una implementación completa, aquí se generarían reportes para el usuario
    return render_template('dashboard.html')  # Temporalmente redirigimos al dashboard

@dashboard_bp.route('/suscripcion')
@login_required
def suscripcion():
    # En una implementación completa, aquí se gestionaría la suscripción del usuario
    return render_template('dashboard.html')  # Temporalmente redirigimos al dashboard

@dashboard_bp.route('/configuracion')
@login_required
def configuracion():
    # En una implementación completa, aquí se gestionaría la configuración del usuario
    return render_template('dashboard.html')  # Temporalmente redirigimos al dashboard

@dashboard_bp.route('/ayuda')
@login_required
def ayuda():
    # En una implementación completa, aquí se mostraría la ayuda al usuario
    return render_template('dashboard.html')  # Temporalmente redirigimos al dashboard
