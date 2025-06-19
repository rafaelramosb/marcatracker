from flask import Blueprint, request, jsonify, session
from src.models import Trademark, SimilarMark, db
import uuid
from datetime import datetime

trademark_bp = Blueprint('trademark', __name__, url_prefix='/api/trademarks')

# Middleware para verificar autenticación
def auth_required(f):
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@trademark_bp.route('/', methods=['GET'])
@auth_required
def get_trademarks():
    """Obtiene todas las marcas del usuario autenticado."""
    user_id = session['user_id']
    
    # Obtener parámetros de paginación y filtrado
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    # Construir consulta base
    query = Trademark.query.filter_by(user_id=user_id)
    
    # Aplicar filtros si existen
    if status:
        query = query.filter_by(status=status)
    
    # Ejecutar consulta paginada
    trademarks = query.order_by(Trademark.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Formatear resultados
    result = {
        'items': [{
            'id': tm.id,
            'name': tm.name,
            'description': tm.description,
            'registration_number': tm.registration_number,
            'application_number': tm.application_number,
            'application_date': tm.application_date.isoformat() if tm.application_date else None,
            'registration_date': tm.registration_date.isoformat() if tm.registration_date else None,
            'expiration_date': tm.expiration_date.isoformat() if tm.expiration_date else None,
            'status': tm.status,
            'nice_classification': tm.nice_classification,
            'logo_path': tm.logo_path,
            'created_at': tm.created_at.isoformat()
        } for tm in trademarks.items],
        'total': trademarks.total,
        'pages': trademarks.pages,
        'current_page': page
    }
    
    return jsonify(result), 200

@trademark_bp.route('/', methods=['POST'])
@auth_required
def create_trademark():
    """Crea una nueva marca para el usuario autenticado."""
    user_id = session['user_id']
    data = request.get_json()
    
    # Validar datos requeridos
    if 'name' not in data:
        return jsonify({'error': 'El nombre de la marca es requerido'}), 400
    
    # Crear nueva marca
    new_trademark = Trademark(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=data['name'],
        description=data.get('description'),
        registration_number=data.get('registration_number'),
        application_number=data.get('application_number'),
        application_date=datetime.fromisoformat(data['application_date']) if data.get('application_date') else None,
        registration_date=datetime.fromisoformat(data['registration_date']) if data.get('registration_date') else None,
        expiration_date=datetime.fromisoformat(data['expiration_date']) if data.get('expiration_date') else None,
        status=data.get('status', 'en seguimiento'),
        nice_classification=data.get('nice_classification'),
        logo_path=data.get('logo_path')
    )
    
    # Guardar en la base de datos
    try:
        db.session.add(new_trademark)
        db.session.commit()
        return jsonify({
            'message': 'Marca creada exitosamente',
            'trademark_id': new_trademark.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear marca: {str(e)}'}), 500

@trademark_bp.route('/<trademark_id>', methods=['GET'])
@auth_required
def get_trademark(trademark_id):
    """Obtiene los detalles de una marca específica."""
    user_id = session['user_id']
    
    # Buscar la marca
    trademark = Trademark.query.filter_by(id=trademark_id, user_id=user_id).first()
    if not trademark:
        return jsonify({'error': 'Marca no encontrada'}), 404
    
    # Obtener marcas similares
    similar_marks = SimilarMark.query.filter_by(trademark_id=trademark_id).all()
    
    # Formatear resultado
    result = {
        'id': trademark.id,
        'name': trademark.name,
        'description': trademark.description,
        'registration_number': trademark.registration_number,
        'application_number': trademark.application_number,
        'application_date': trademark.application_date.isoformat() if trademark.application_date else None,
        'registration_date': trademark.registration_date.isoformat() if trademark.registration_date else None,
        'expiration_date': trademark.expiration_date.isoformat() if trademark.expiration_date else None,
        'status': trademark.status,
        'nice_classification': trademark.nice_classification,
        'logo_path': trademark.logo_path,
        'created_at': trademark.created_at.isoformat(),
        'similar_marks': [{
            'id': sm.id,
            'name': sm.name,
            'registration_number': sm.registration_number,
            'application_number': sm.application_number,
            'application_date': sm.application_date.isoformat() if sm.application_date else None,
            'nice_classification': sm.nice_classification,
            'similarity_score': sm.similarity_score,
            'similarity_type': sm.similarity_type,
            'source': sm.source,
            'source_url': sm.source_url,
            'logo_path': sm.logo_path,
            'created_at': sm.created_at.isoformat()
        } for sm in similar_marks]
    }
    
    return jsonify(result), 200

@trademark_bp.route('/<trademark_id>', methods=['PUT'])
@auth_required
def update_trademark(trademark_id):
    """Actualiza una marca existente."""
    user_id = session['user_id']
    
    # Buscar la marca
    trademark = Trademark.query.filter_by(id=trademark_id, user_id=user_id).first()
    if not trademark:
        return jsonify({'error': 'Marca no encontrada'}), 404
    
    data = request.get_json()
    
    # Actualizar campos permitidos
    if 'name' in data:
        trademark.name = data['name']
    if 'description' in data:
        trademark.description = data['description']
    if 'registration_number' in data:
        trademark.registration_number = data['registration_number']
    if 'application_number' in data:
        trademark.application_number = data['application_number']
    if 'application_date' in data:
        trademark.application_date = datetime.fromisoformat(data['application_date']) if data['application_date'] else None
    if 'registration_date' in data:
        trademark.registration_date = datetime.fromisoformat(data['registration_date']) if data['registration_date'] else None
    if 'expiration_date' in data:
        trademark.expiration_date = datetime.fromisoformat(data['expiration_date']) if data['expiration_date'] else None
    if 'status' in data:
        trademark.status = data['status']
    if 'nice_classification' in data:
        trademark.nice_classification = data['nice_classification']
    if 'logo_path' in data:
        trademark.logo_path = data['logo_path']
    
    # Guardar cambios
    try:
        db.session.commit()
        return jsonify({'message': 'Marca actualizada exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar marca: {str(e)}'}), 500

@trademark_bp.route('/<trademark_id>', methods=['DELETE'])
@auth_required
def delete_trademark(trademark_id):
    """Elimina una marca existente."""
    user_id = session['user_id']
    
    # Buscar la marca
    trademark = Trademark.query.filter_by(id=trademark_id, user_id=user_id).first()
    if not trademark:
        return jsonify({'error': 'Marca no encontrada'}), 404
    
    # Eliminar marca y sus relaciones
    try:
        # Primero eliminar marcas similares relacionadas
        SimilarMark.query.filter_by(trademark_id=trademark_id).delete()
        
        # Luego eliminar la marca
        db.session.delete(trademark)
        db.session.commit()
        return jsonify({'message': 'Marca eliminada exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar marca: {str(e)}'}), 500
