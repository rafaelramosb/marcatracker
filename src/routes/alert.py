from flask import Blueprint, request, jsonify, session
from src.models import Alert, Trademark, User, db
import uuid

alert_bp = Blueprint('alert', __name__, url_prefix='/api/alerts')

# Middleware para verificar autenticación
def auth_required(f):
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@alert_bp.route('/', methods=['GET'])
@auth_required
def get_alerts():
    """Obtiene todas las alertas del usuario autenticado."""
    user_id = session['user_id']
    
    # Obtener parámetros de paginación y filtrado
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    trademark_id = request.args.get('trademark_id')
    
    # Construir consulta base
    query = Alert.query.filter_by(user_id=user_id)
    
    # Aplicar filtros si existen
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if trademark_id:
        query = query.filter_by(trademark_id=trademark_id)
    
    # Ejecutar consulta paginada
    alerts = query.order_by(Alert.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Formatear resultados
    result = {
        'items': [{
            'id': alert.id,
            'title': alert.title,
            'description': alert.description,
            'alert_type': alert.alert_type,
            'priority': alert.priority,
            'status': alert.status,
            'trademark_id': alert.trademark_id,
            'similar_mark_id': alert.similar_mark_id,
            'created_at': alert.created_at.isoformat()
        } for alert in alerts.items],
        'total': alerts.total,
        'pages': alerts.pages,
        'current_page': page
    }
    
    return jsonify(result), 200

@alert_bp.route('/<alert_id>', methods=['GET'])
@auth_required
def get_alert(alert_id):
    """Obtiene los detalles de una alerta específica."""
    user_id = session['user_id']
    
    # Buscar la alerta
    alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()
    if not alert:
        return jsonify({'error': 'Alerta no encontrada'}), 404
    
    # Obtener información relacionada
    trademark = Trademark.query.get(alert.trademark_id)
    
    # Formatear resultado
    result = {
        'id': alert.id,
        'title': alert.title,
        'description': alert.description,
        'alert_type': alert.alert_type,
        'priority': alert.priority,
        'status': alert.status,
        'created_at': alert.created_at.isoformat(),
        'trademark': {
            'id': trademark.id,
            'name': trademark.name,
            'registration_number': trademark.registration_number,
            'nice_classification': trademark.nice_classification,
            'status': trademark.status
        } if trademark else None
    }
    
    # Marcar como vista si es nueva
    if alert.status == 'nueva':
        alert.status = 'vista'
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    
    return jsonify(result), 200

@alert_bp.route('/<alert_id>/status', methods=['PUT'])
@auth_required
def update_alert_status(alert_id):
    """Actualiza el estado de una alerta."""
    user_id = session['user_id']
    data = request.get_json()
    
    # Validar datos requeridos
    if 'status' not in data:
        return jsonify({'error': 'El estado es requerido'}), 400
    
    # Validar estado válido
    valid_statuses = ['nueva', 'vista', 'resuelta', 'ignorada']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Estado inválido. Debe ser uno de: {", ".join(valid_statuses)}'}), 400
    
    # Buscar la alerta
    alert = Alert.query.filter_by(id=alert_id, user_id=user_id).first()
    if not alert:
        return jsonify({'error': 'Alerta no encontrada'}), 404
    
    # Actualizar estado
    alert.status = data['status']
    
    # Guardar cambios
    try:
        db.session.commit()
        return jsonify({'message': 'Estado de alerta actualizado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar estado: {str(e)}'}), 500

@alert_bp.route('/summary', methods=['GET'])
@auth_required
def get_alert_summary():
    """Obtiene un resumen de las alertas del usuario."""
    user_id = session['user_id']
    
    # Contar alertas por estado
    new_count = Alert.query.filter_by(user_id=user_id, status='nueva').count()
    seen_count = Alert.query.filter_by(user_id=user_id, status='vista').count()
    resolved_count = Alert.query.filter_by(user_id=user_id, status='resuelta').count()
    ignored_count = Alert.query.filter_by(user_id=user_id, status='ignorada').count()
    
    # Contar alertas por prioridad
    high_priority = Alert.query.filter_by(user_id=user_id, priority='alta').count()
    medium_priority = Alert.query.filter_by(user_id=user_id, priority='media').count()
    low_priority = Alert.query.filter_by(user_id=user_id, priority='baja').count()
    
    result = {
        'total': new_count + seen_count + resolved_count + ignored_count,
        'by_status': {
            'nueva': new_count,
            'vista': seen_count,
            'resuelta': resolved_count,
            'ignorada': ignored_count
        },
        'by_priority': {
            'alta': high_priority,
            'media': medium_priority,
            'baja': low_priority
        }
    }
    
    return jsonify(result), 200
