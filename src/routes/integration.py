from flask import Blueprint, request, jsonify, session
from src.models import DataSource, DataSyncLog, db
import uuid
from datetime import datetime

integration_bp = Blueprint('integration', __name__, url_prefix='/api/integration')

# Middleware para verificar autenticación y permisos de administrador
def admin_required(f):
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        
        # Verificar si es administrador
        from src.models import User
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Acceso denegado. Se requieren permisos de administrador'}), 403
        
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@integration_bp.route('/sources', methods=['GET'])
@admin_required
def get_data_sources():
    """Obtiene todas las fuentes de datos configuradas."""
    sources = DataSource.query.all()
    
    result = [{
        'id': source.id,
        'name': source.name,
        'description': source.description,
        'source_type': source.source_type,
        'url': source.url,
        'auth_required': source.auth_required,
        'last_sync': source.last_sync.isoformat() if source.last_sync else None,
        'sync_frequency': source.sync_frequency,
        'is_active': source.is_active,
        'created_at': source.created_at.isoformat()
    } for source in sources]
    
    return jsonify(result), 200

@integration_bp.route('/sources', methods=['POST'])
@admin_required
def create_data_source():
    """Crea una nueva fuente de datos."""
    data = request.get_json()
    
    # Validar datos requeridos
    required_fields = ['name', 'source_type', 'url', 'sync_frequency']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Crear nueva fuente de datos
    new_source = DataSource(
        id=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description'),
        source_type=data['source_type'],
        url=data['url'],
        auth_required=data.get('auth_required', False),
        auth_credentials=data.get('auth_credentials'),
        sync_frequency=data['sync_frequency'],
        is_active=data.get('is_active', True)
    )
    
    # Guardar en la base de datos
    try:
        db.session.add(new_source)
        db.session.commit()
        return jsonify({
            'message': 'Fuente de datos creada exitosamente',
            'source_id': new_source.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear fuente de datos: {str(e)}'}), 500

@integration_bp.route('/sources/<source_id>', methods=['PUT'])
@admin_required
def update_data_source(source_id):
    """Actualiza una fuente de datos existente."""
    # Buscar la fuente de datos
    source = DataSource.query.get(source_id)
    if not source:
        return jsonify({'error': 'Fuente de datos no encontrada'}), 404
    
    data = request.get_json()
    
    # Actualizar campos permitidos
    if 'name' in data:
        source.name = data['name']
    if 'description' in data:
        source.description = data['description']
    if 'source_type' in data:
        source.source_type = data['source_type']
    if 'url' in data:
        source.url = data['url']
    if 'auth_required' in data:
        source.auth_required = data['auth_required']
    if 'auth_credentials' in data:
        source.auth_credentials = data['auth_credentials']
    if 'sync_frequency' in data:
        source.sync_frequency = data['sync_frequency']
    if 'is_active' in data:
        source.is_active = data['is_active']
    
    # Guardar cambios
    try:
        db.session.commit()
        return jsonify({'message': 'Fuente de datos actualizada exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al actualizar fuente de datos: {str(e)}'}), 500

@integration_bp.route('/sources/<source_id>/sync', methods=['POST'])
@admin_required
def trigger_sync(source_id):
    """Inicia manualmente una sincronización con la fuente de datos."""
    # Buscar la fuente de datos
    source = DataSource.query.get(source_id)
    if not source:
        return jsonify({'error': 'Fuente de datos no encontrada'}), 404
    
    # Verificar si está activa
    if not source.is_active:
        return jsonify({'error': 'La fuente de datos no está activa'}), 400
    
    # Crear registro de sincronización
    sync_log = DataSyncLog(
        id=str(uuid.uuid4()),
        data_source_id=source_id,
        start_time=datetime.utcnow(),
        status='en_proceso'
    )
    
    # Guardar en la base de datos
    try:
        db.session.add(sync_log)
        db.session.commit()
        
        # Aquí se iniciaría el proceso de sincronización en segundo plano
        # Por ahora, solo simulamos el inicio del proceso
        
        return jsonify({
            'message': 'Sincronización iniciada exitosamente',
            'sync_id': sync_log.id
        }), 202
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al iniciar sincronización: {str(e)}'}), 500

@integration_bp.route('/logs', methods=['GET'])
@admin_required
def get_sync_logs():
    """Obtiene los registros de sincronización."""
    # Obtener parámetros de paginación y filtrado
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    source_id = request.args.get('source_id')
    status = request.args.get('status')
    
    # Construir consulta base
    query = DataSyncLog.query
    
    # Aplicar filtros si existen
    if source_id:
        query = query.filter_by(data_source_id=source_id)
    if status:
        query = query.filter_by(status=status)
    
    # Ejecutar consulta paginada
    logs = query.order_by(DataSyncLog.start_time.desc()).paginate(page=page, per_page=per_page)
    
    # Formatear resultados
    result = {
        'items': [{
            'id': log.id,
            'data_source_id': log.data_source_id,
            'start_time': log.start_time.isoformat(),
            'end_time': log.end_time.isoformat() if log.end_time else None,
            'status': log.status,
            'records_processed': log.records_processed,
            'records_added': log.records_added,
            'error_message': log.error_message
        } for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    }
    
    return jsonify(result), 200
