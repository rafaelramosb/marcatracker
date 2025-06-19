from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Validar datos
        if not email or not password:
            error = 'Por favor ingresa todos los campos requeridos.'
            return render_template('login.html', error=error)
        
        # Buscar usuario en la base de datos
        user = User.query.filter_by(email=email).first()
        
        # Verificar si el usuario existe y la contraseña es correcta
        if not user or not check_password_hash(user.password, password):
            error = 'Credenciales incorrectas. Por favor verifica tu correo y contraseña.'
            return render_template('login.html', error=error)
        
        # Si todo está bien, iniciar sesión
        session['user_id'] = user.id
        session['user_name'] = user.nombre
        session['user_email'] = user.email
        
        # Actualizar último acceso
        user.ultimo_acceso = datetime.utcnow()
        db.session.commit()
        
        # Redirigir al dashboard
        return redirect(url_for('dashboard.index'))
    
    return render_template('login.html', error=error)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    error = None
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        plan = request.form.get('plan')
        terminos = request.form.get('terminos')
        
        # Validar datos
        if not nombre or not apellido or not email or not password or not confirm_password or not plan:
            error = 'Por favor completa todos los campos requeridos.'
            return render_template('registro.html', error=error)
        
        if password != confirm_password:
            error = 'Las contraseñas no coinciden.'
            return render_template('registro.html', error=error)
        
        if not terminos:
            error = 'Debes aceptar los términos y condiciones para continuar.'
            return render_template('registro.html', error=error)
        
        # Verificar si el correo ya está registrado
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error = 'Este correo electrónico ya está registrado. Por favor utiliza otro o inicia sesión.'
            return render_template('registro.html', error=error)
        
        # Crear nuevo usuario
        new_user = User(
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            plan=plan,
            fecha_registro=datetime.utcnow(),
            ultimo_acceso=datetime.utcnow(),
            activo=True
        )
        
        # Guardar en la base de datos
        db.session.add(new_user)
        db.session.commit()
        
        # Iniciar sesión automáticamente
        session['user_id'] = new_user.id
        session['user_name'] = new_user.nombre
        session['user_email'] = new_user.email
        
        # Redirigir al dashboard
        return redirect(url_for('dashboard.index'))
    
    # Si es GET o hay error, mostrar formulario
    return render_template('registro.html', error=error)

@auth_bp.route('/logout')
def logout():
    # Eliminar datos de sesión
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    
    # Redirigir a la página principal
    return redirect(url_for('index'))

@auth_bp.route('/recuperar-password', methods=['GET', 'POST'])
def recuperar_password():
    # Implementación básica para recuperación de contraseña
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Verificar si el correo existe
        user = User.query.filter_by(email=email).first()
        if user:
            # En una implementación real, aquí enviaríamos un correo con instrucciones
            # Para esta demo, simplemente mostramos un mensaje
            flash('Se han enviado instrucciones para restablecer tu contraseña a tu correo electrónico.', 'success')
        else:
            flash('No se encontró ninguna cuenta con ese correo electrónico.', 'danger')
        
        return redirect(url_for('auth.login'))
    
    return render_template('recuperar_password.html')
