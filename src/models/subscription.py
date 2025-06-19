from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from .user import db

class Subscription(db.Model):
    """Modelo para las suscripciones de los usuarios."""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    auto_renew = db.Column(db.Boolean, default=True)
    payment_status = db.Column(db.String(20), nullable=False, default='pending')
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', back_populates='subscriptions')
    plan = db.relationship('SubscriptionPlan')
    
    def __repr__(self):
        return f'<Subscription {self.id} - User: {self.user_id}>'


class SubscriptionPlan(db.Model):
    """Modelo para los planes de suscripción disponibles."""
    
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    max_trademarks = db.Column(db.Integer, nullable=False)
    features = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'
