from flask import Blueprint, request, jsonify, session
from src.models import Subscription, SubscriptionPlan, User, db
import uuid
from datetime import datetime, timedelta

subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscriptions')

# Middleware para verificar autenticación
def auth_required(f):
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@subscription_bp.route('/plans', methods=['GET'])
def get_plans():
    """Obtiene todos los planes de suscripción disponibles."""
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    
    result = [{
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'price': plan.price,
        'duration_months': plan.duration_months,
        'max_trademarks': plan.max_trademarks,
        'features': plan.features,
        'is_premium': plan.is_premium
    } for plan in plans]
    
    return jsonify(result), 200

@subscription_bp.route('/my-subscription', methods=['GET'])
@auth_required
def get_user_subscription():
    """Obtiene la suscripción activa del usuario."""
    user_id = session['user_id']
    
    # Buscar suscripción activa
    subscription = Subscription.query.filter_by(
        user_id=user_id, 
        is_active=True
    ).order_by(Subscription.end_date.desc()).first()
    
    if not subscription:
        return jsonify({'message': 'No tiene una suscripción activa'}), 404
    
    # Obtener detalles del plan
    plan = SubscriptionPlan.query.get(subscription.plan_id)
    
    result = {
        'id': subscription.id,
        'start_date': subscription.start_date.isoformat(),
        'end_date': subscription.end_date.isoformat(),
        'is_active': subscription.is_active,
        'auto_renew': subscription.auto_renew,
        'payment_status': subscription.payment_status,
        'plan': {
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'price': plan.price,
            'duration_months': plan.duration_months,
            'max_trademarks': plan.max_trademarks,
            'features': plan.features,
            'is_premium': plan.is_premium
        }
    }
    
    return jsonify(result), 200

@subscription_bp.route('/subscribe', methods=['POST'])
@auth_required
def create_subscription():
    """Crea una nueva suscripción para el usuario."""
    user_id = session['user_id']
    data = request.get_json()
    
    # Validar datos requeridos
    if 'plan_id' not in data:
        return jsonify({'error': 'El ID del plan es requerido'}), 400
    
    # Verificar si el plan existe
    plan = SubscriptionPlan.query.filter_by(id=data['plan_id'], is_active=True).first()
    if not plan:
        return jsonify({'error': 'Plan no encontrado o no disponible'}), 404
    
    # Verificar si ya tiene una suscripción activa
    active_subscription = Subscription.query.filter_by(
        user_id=user_id, 
        is_active=True
    ).first()
    
    if active_subscription:
        # Desactivar suscripción anterior si existe
        active_subscription.is_active = False
        active_subscription.auto_renew = False
    
    # Calcular fechas
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=30 * plan.duration_months)
    
    # Crear nueva suscripción
    new_subscription = Subscription(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        auto_renew=data.get('auto_renew', True),
        payment_status='pendiente',
        payment_method=data.get('payment_method'),
        payment_reference=data.get('payment_reference')
    )
    
    # Guardar en la base de datos
    try:
        db.session.add(new_subscription)
        db.session.commit()
        return jsonify({
            'message': 'Suscripción creada exitosamente',
            'subscription_id': new_subscription.id,
            'payment_status': 'pendiente'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear suscripción: {str(e)}'}), 500

@subscription_bp.route('/<subscription_id>/confirm-payment', methods=['POST'])
@auth_required
def confirm_payment(subscription_id):
    """Confirma el pago de una suscripción."""
    user_id = session['user_id']
    data = request.get_json()
    
    # Buscar la suscripción
    subscription = Subscription.query.filter_by(id=subscription_id, user_id=user_id).first()
    if not subscription:
        return jsonify({'error': 'Suscripción no encontrada'}), 404
    
    # Actualizar estado de pago
    subscription.payment_status = 'completado'
    subscription.payment_reference = data.get('payment_reference', subscription.payment_reference)
    
    # Guardar cambios
    try:
        db.session.commit()
        return jsonify({'message': 'Pago confirmado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al confirmar pago: {str(e)}'}), 500

@subscription_bp.route('/<subscription_id>/cancel', methods=['POST'])
@auth_required
def cancel_subscription(subscription_id):
    """Cancela una suscripción activa."""
    user_id = session['user_id']
    
    # Buscar la suscripción
    subscription = Subscription.query.filter_by(id=subscription_id, user_id=user_id).first()
    if not subscription:
        return jsonify({'error': 'Suscripción no encontrada'}), 404
    
    # Verificar si está activa
    if not subscription.is_active:
        return jsonify({'error': 'La suscripción ya está cancelada'}), 400
    
    # Cancelar renovación automática
    subscription.auto_renew = False
    
    # Guardar cambios
    try:
        db.session.commit()
        return jsonify({'message': 'Renovación automática cancelada exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al cancelar suscripción: {str(e)}'}), 500

# Ruta para administradores
@subscription_bp.route('/admin/plans', methods=['POST'])
@auth_required
def create_plan():
    """Crea un nuevo plan de suscripción (solo administradores)."""
    user_id = session['user_id']
    
    # Verificar si es administrador
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    data = request.get_json()
    
    # Validar datos requeridos
    required_fields = ['name', 'price', 'duration_months', 'max_trademarks']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'El campo {field} es requerido'}), 400
    
    # Crear nuevo plan
    new_plan = SubscriptionPlan(
        id=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        duration_months=data['duration_months'],
        max_trademarks=data['max_trademarks'],
        features=data.get('features'),
        is_active=data.get('is_active', True),
        is_premium=data.get('is_premium', False)
    )
    
    # Guardar en la base de datos
    try:
        db.session.add(new_plan)
        db.session.commit()
        return jsonify({
            'message': 'Plan creado exitosamente',
            'plan_id': new_plan.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear plan: {str(e)}'}), 500
