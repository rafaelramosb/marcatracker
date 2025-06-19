from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from .user import db

class Trademark(db.Model):
    """Modelo para las marcas registradas o en seguimiento."""
    
    __tablename__ = 'trademarks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    registration_number = db.Column(db.String(50), nullable=True)
    application_number = db.Column(db.String(50), nullable=True)
    application_date = db.Column(db.DateTime, nullable=True)
    registration_date = db.Column(db.DateTime, nullable=True)
    expiration_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='en seguimiento')
    nice_classification = db.Column(db.String(50), nullable=True)
    logo_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', back_populates='trademarks')
    alerts = db.relationship('Alert', back_populates='trademark', lazy=True)
    similar_marks = db.relationship('SimilarMark', back_populates='trademark', lazy=True)
    logo_images = db.relationship('LogoImage', back_populates='trademark', lazy=True)
    
    def __repr__(self):
        return f'<Trademark {self.name}>'


class SimilarMark(db.Model):
    """Modelo para marcas similares detectadas."""
    
    __tablename__ = 'similar_marks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trademark_id = db.Column(db.String(36), db.ForeignKey('trademarks.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(50), nullable=True)
    application_number = db.Column(db.String(50), nullable=True)
    application_date = db.Column(db.DateTime, nullable=True)
    nice_classification = db.Column(db.String(50), nullable=True)
    similarity_score = db.Column(db.Float, nullable=False)
    similarity_type = db.Column(db.String(50), nullable=False)  # nombre, imagen, fonética
    source = db.Column(db.String(50), nullable=False)  # gaceta, sic_web, datos_abiertos
    source_url = db.Column(db.String(255), nullable=True)
    logo_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    trademark = db.relationship('Trademark', back_populates='similar_marks')
    
    def __repr__(self):
        return f'<SimilarMark {self.name} - Score: {self.similarity_score}>'


class GacetaDocument(db.Model):
    """Modelo para almacenar referencias a documentos de la Gaceta"""
    
    __tablename__ = 'gaceta_documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    download_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processing_date = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<GacetaDocument {self.filename}>'


class LogoImage(db.Model):
    """Modelo para almacenar referencias a imágenes de logos"""
    
    __tablename__ = 'logo_images'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trademark_id = db.Column(db.String(36), db.ForeignKey('trademarks.id'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    source_url = db.Column(db.String(512), nullable=True)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    trademark = db.relationship('Trademark', back_populates='logo_images')
    
    def __repr__(self):
        return f'<LogoImage {self.filename}>'
