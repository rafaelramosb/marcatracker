from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from .user import db
from .trademark import Trademark

class Alert(db.Model):
    """Modelo para las alertas generadas por el sistema."""
    
    __tablename__ = 'alerts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    trademark_id = db.Column(db.String(36), db.ForeignKey('trademarks.id'), nullable=False)
    similar_mark_id = db.Column(db.String(36), db.ForeignKey('similar_marks.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # similitud, vencimiento, cambio_estado
    priority = db.Column(db.String(20), nullable=False, default='media')  # alta, media, baja
    status = db.Column(db.String(20), nullable=False, default='nueva')  # nueva, vista, resuelta, ignorada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', back_populates='alerts')
    trademark = db.relationship('Trademark', back_populates='alerts')
    
    def __repr__(self):
        return f'<Alert {self.title} - Type: {self.alert_type}>'


class DataSource(db.Model):
    """Modelo para las fuentes de datos utilizadas por el sistema."""
    
    __tablename__ = 'data_sources'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    source_type = db.Column(db.String(50), nullable=False)  # gaceta, sic_web, datos_abiertos, api
    url = db.Column(db.String(255), nullable=False)
    auth_required = db.Column(db.Boolean, default=False)
    auth_credentials = db.Column(db.Text, nullable=True)
    last_sync = db.Column(db.DateTime, nullable=True)
    sync_frequency = db.Column(db.Integer, nullable=False, default=24)  # horas
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    sync_logs = db.relationship('DataSyncLog', back_populates='data_source', lazy=True)
    
    def __repr__(self):
        return f'<DataSource {self.name} - Type: {self.source_type}>'


class DataSyncLog(db.Model):
    """Modelo para los registros de sincronización con fuentes de datos."""
    
    __tablename__ = 'data_sync_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = db.Column(db.String(36), db.ForeignKey('data_sources.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='en_proceso')  # en_proceso, completado, error
    records_processed = db.Column(db.Integer, nullable=True)
    records_added = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Relaciones
    data_source = db.relationship('DataSource', back_populates='sync_logs')
    
    def __repr__(self):
        return f'<DataSyncLog {self.id} - Status: {self.status}>'
