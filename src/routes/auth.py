from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import User, db
import uuid

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registra un nuevo usuario en el sistema."""
    data = request.get_json()
    
    # Validar datos requeridos
    required_fields = ['email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Verificar si el correo ya está registrado
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Este correo electrónico ya está registrado'}), 400
    
    # Crear nuevo usuario
    new_user = User(
        id=str(uuid.uuid4()),
        email=data['email'],
        password=generate_password_hash(data['password']),
        first_name=data['first_name'],
        last_name=data['last_name'],
        company_name=data.get('company_name'),
        phone=data.get('phone')
    )
    
    # Guardar en la base de datos
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user_id': new_user.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al registrar usuario: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Inicia sesión de usuario."""
    data = request.get_json()
    
    # Validar datos requeridos
    if 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Correo y contraseña son requeridos'}), 400
    
    # Buscar usuario por correo
    user = User.query.filter_by(email=data['email']).first()
    
    # Verificar si el usuario existe y la contraseña es correcta
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    # Verificar si el usuario está activo
    if not user.is_active:
        return jsonify({'error': 'Cuenta desactivada. Contacte al administrador'}), 403
    
    # Crear sesión
    session['user_id'] = user.id
    
    return jsonify({
        'message': 'Inicio de sesión exitoso',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_admin': user.is_admin
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Cierra la sesión del usuario."""
    session.pop('user_id', None)
    return jsonify({'message': 'Sesión cerrada exitosamente'}), 200

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Obtiene el perfil del usuario autenticado."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'company_name': user.company_name,
        'phone': user.phone,
        'created_at': user.created_at.isoformat(),
        'is_admin': user.is_admin
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Actualiza el perfil del usuario autenticado."""
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    data = request.get_json()
    
    # Actualizar campos permitidos
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'company_name' in data:
        user.company_name = data['company_name']
    if 'phone' in data:
        user.phone = data['phone']
    
    # Actualizar contraseña si se proporciona
    if 'password' in data and data['password']:
        user.password = generate_password_hash(data['password'])
    
    try:
        db.session.commit()
        return jsonify({'message': 'Perfil actualizado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar perfil: {str(e)}'}), 500
